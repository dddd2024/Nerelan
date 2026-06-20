```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_training_capability_gap_matrix_closeout_rework_v1",
  "round_id": "round_20260621_training_capability_gap_matrix_closeout_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the failed closeout/audit state for `decision_20260620_training_capability_gap_matrix_v1` without expanding scope. Preserve the generated training capability gap matrix and next static-triage plan if their contents still pass metadata-only constraints, but fix the reporting, pytest summary, gate artifacts, and closeout consistency so the round is auditable.

This is a cleanup/rework round. Do not solve samples.

## 2. Current Evidence

The previous round generated useful metadata-only planning artifacts:

- `project_state/local_reverse_training_capability_gap_matrix.json`
- `project_state/local_reverse_training_capability_gap_matrix_report.md`
- `project_state/local_reverse_next_static_triage_plan.json`
- `project_state/local_reverse_next_static_triage_plan_report.md`

However, the round failed because:

- `codex_execution_report.md` reports `FAILED` and `REWORK_REQUIRED`;
- Required Audit answers for the training-dataset decision are missing or not aligned;
- `pytest_result.txt` top summary points to the previous command-plan rework decision, not the current training capability matrix decision;
- `final_gate_result.json` is `FAILED`;
- `report_summary_synthesis.json` disagrees with `codex_report_summary`;
- `command_plan.json` recommends manual follow-up instead of the decision-required run-closeout path;
- stale gate artifacts reference the previous round;
- round archive/manifest state is inconsistent or missing.

The generated matrix and plan may be reused only after confirming that they do not claim solved/static_verified/runtime_validated status and that they remain metadata-only planning artifacts.

## 3. Do Not Do

Do not continue `samplereverse` solving.

Do not run samples, binaries, runtime probes, harnesses, debuggers, emulators, GUI workflows, IDA, Ghidra, x64dbg, or OllyDbg.

Do not scan full `solve_reports/`.

Do not modify source files unless a narrow gate bug is found; if source modification is required, stop and report BLOCKED instead of changing source.

Do not rewrite `.codex-skills/`.

Do not regenerate unrelated project_state files.

Do not mark any sample as solved, static_verified, runtime_validated, or solver_ready unless that status already has current evidence and is explicitly part of the existing artifact.

Do not claim SUCCESS unless report-summary and final-check pass for the current rework decision.

## 4. Files To Inspect

Default state:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Failed-round artifacts:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/final_gate_result.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/gate_profile_plan.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/rounds/round_20260620_training_capability_gap_matrix_v1/*` if present

Generated training artifacts:

1. `project_state/local_reverse_training_capability_gap_matrix.json`
2. `project_state/local_reverse_training_capability_gap_matrix_report.md`
3. `project_state/local_reverse_next_static_triage_plan.json`
4. `project_state/local_reverse_next_static_triage_plan_report.md`

## 5. Required Audit

Before editing, answer in the new `codex_execution_report.md`:

1. Which exact gate failures caused the previous round to be non-acceptable?
2. Which generated training artifacts can be preserved, and why?
3. Does the capability gap matrix still avoid solved/static_verified/runtime_validated claims?
4. Does the next static-triage plan remain bounded to at most three items?
5. Why did `pytest_result.txt` mismatch the active report/decision?
6. Which stale IDs exist in gate artifacts, and how will the rework avoid carrying them forward?
7. Whether `run-closeout` is actually required and permitted under the current command-plan/gate profile; if there is a contradiction, stop and report BLOCKED rather than fabricating success.
8. How the final report will prove no samples, tools, debuggers, dynamic validation, solvers, or full `solve_reports/` scan were run.

## 6. Implementation Scope

Artifact/report cleanup only.

Required actions:

1. Rewrite `project_state/codex_execution_report.md` for this rework round with a correct `codex_report_summary`.
2. Rewrite `project_state/pytest_result.txt` so its structured summary matches the rework decision/report/round IDs.
3. Regenerate or update gate artifacts only through allowed project gate commands.
4. Ensure `files_changed`, `generated_artifacts`, and `referenced_artifacts` exactly match actual round delta and preserved artifacts.
5. If preserving the previous matrix/plan, list them as referenced or generated artifacts consistently according to gate policy.
6. Ensure Required Audit answers are substantive and specific to the training-dataset rework.
7. Do not change the matrix/plan content unless needed to correct metadata-only claims or artifact bookkeeping.

Allowed changed files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260621_training_capability_gap_matrix_closeout_rework_v1/*`
- The four training artifacts only if bookkeeping or non-promotion wording must be corrected.

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
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Only run pytest if the command-plan or gate profile requires it. If pytest is run, record the exact command and result in `project_state/pytest_result.txt`.

Only run closeout if command-plan and gate profile both permit it. If decision contract and gate profile disagree, stop with BLOCKED.

## 8. Stop Conditions

Stop and report `BLOCKED` if:

1. command-plan forbids closeout but decision contract requires closeout;
2. final-check still references stale decision/report/round IDs;
3. `pytest_result.txt` cannot be made to match current report/decision IDs;
4. Required Audit answers cannot be completed from current state without running forbidden tools;
5. fixing the issue requires source changes;
6. any sample/runtime/debugger/harness/IDA/Ghidra execution would be needed;
7. report-summary still differs from `codex_report_summary`;
8. final-check fails after the rework.

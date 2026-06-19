```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_staged_state_artifact_closeout_v1",
  "round_id": "round_20260619_staged_state_artifact_closeout_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close the staged state rebuild workflow correctly by making its generated artifacts explicit, inspectable, and covered by report/gate evidence.

The previous round implemented `rebuild-stage` in code and tests passed, but the expected artifacts were not present in GitHub and were not listed in `codex_report_summary.generated_artifacts`. This round must either generate and register the staged artifacts, or document a precise blocker explaining why they cannot be committed.

This is an engineering closeout round. Do not continue reverse solving, do not run live state build, and do not mutate live compact state root files.

Success criteria:

1. `state_rebuild_apply_plan.json` is present, inspectable, and listed in report/gate evidence, or a precise blocker explains why it cannot be present.
2. Proposed staged state files are present and inspectable, or archived under the current round and listed in report/gate evidence.
3. `codex_report_summary.files_changed` and `generated_artifacts` match the actual staged/apply-plan artifact paths.
4. Live root state files remain unmodified unless the decision is explicitly revised later.
5. `final-check` has no FAIL and report/decision/pytest/final-gate IDs match.

## 2. Current Evidence

`decision_20260619_staged_state_rebuild_workflow_v1` reported `SUCCESS / ACCEPTED`, but its structured `generated_artifacts` did not include:

- `project_state/state_rebuild_apply_plan.json`
- `project_state/proposed_state/artifact_index.json`
- `project_state/proposed_state/current_state.json`
- `project_state/proposed_state/negative_results.json`
- `project_state/proposed_state/model_gate.json`
- `project_state/proposed_state/task_packet.json`

Direct GitHub inspection showed `project_state/state_rebuild_apply_plan.json` and `project_state/proposed_state/current_state.json` were not present.

Source implementation for `rebuild_stage()` exists and appears to write proposed state files to a staging directory and apply-plan to `state_dir`.

The previous final gate passed, but it did not prove the staged/apply-plan artifacts were present in GitHub or properly registered in `generated_artifacts`.

`task_packet.json` remains advisory only. This `decision_packet.md` controls the current round.

Negative-results still apply:

- Do not return to old sample_solver blind search.
- Do not only increase beam/budget.
- Do not use compare_semantics_agree=false candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat current 5-candidate transform-trace audit without new runtime evidence.

## 3. Do Not Do

Do not run live `python -m reverse_agent.project_state build` against `project_state`.

Do not mutate live root state files:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/negative_results.json`

Do not continue affine solving.

Do not resume `samplereverse` candidate search.

Do not run binaries, runtime probes, debuggers, emulators, hooks, or dynamic validation.

Do not read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`.

Do not weaken decision-lint or reverse-solving candidate/solution gates.

Do not modify `.codex-skills/`.

Do not claim `SUCCESS` if staged artifacts are generated but not listed in report/gate evidence.

Do not claim staged artifacts exist if they cannot be found either live or archived.

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

1. `reverse_agent/project_state.py`
2. `tests/test_project_state.py`
3. `reverse_agent/project_gate.py`
4. `tests/test_project_gate.py`

Expected staged artifacts:

1. `project_state/state_rebuild_apply_plan.json`
2. `project_state/proposed_state/artifact_index.json`
3. `project_state/proposed_state/current_state.json`
4. `project_state/proposed_state/negative_results.json`
5. `project_state/proposed_state/model_gate.json`
6. `project_state/proposed_state/task_packet.json`

Gate/status artifacts:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/preflight_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/gate_profile_plan.json`

Archive target:

1. `project_state/rounds/round_20260619_staged_state_artifact_closeout_v1/*`

## 5. Required Audit

Before changing code, answer:

1. Were `state_rebuild_apply_plan.json` and `proposed_state/*.json` generated locally in the previous round?
2. Are they omitted because of `.gitignore`, gate filtering, report-summary filtering, or because `rebuild-stage` was only exercised inside tests?
3. Should staged proposed state files be committed to GitHub, or should they be archived only under `rounds/<round_id>/`?
4. Does `generated_artifacts_cover_round_delta` check staged artifacts if they are omitted from `generated_artifacts`?
5. Should final-check require report claims about staged artifacts to match actual generated artifact paths?
6. Can the closeout be fixed artifact-only, or does gate/report logic need a small patch?
7. Did the previous round accidentally omit generated workflow artifacts from `codex_report_summary.generated_artifacts`?
8. Does the new closeout preserve live state immutability?

## 6. Implementation Scope

Preferred implementation is artifact-first closeout.

Required actions:

1. Run `rebuild-stage` explicitly for this round:

```powershell
python -m reverse_agent.project_state rebuild-stage --state-dir project_state --out-dir project_state/proposed_state
```

2. Verify `project_state/state_rebuild_apply_plan.json` exists.
3. Verify the following proposed files exist:
   - `project_state/proposed_state/artifact_index.json`
   - `project_state/proposed_state/current_state.json`
   - `project_state/proposed_state/negative_results.json`
   - `project_state/proposed_state/model_gate.json`
   - `project_state/proposed_state/task_packet.json`
4. Add all staged/apply-plan artifacts to `codex_report_summary.generated_artifacts`.
5. Add all staged/apply-plan artifacts to `codex_report_summary.files_changed` if they are expected to be committed.
6. If staged files should not be committed, archive them under:
   `project_state/rounds/round_20260619_staged_state_artifact_closeout_v1/`
   and list the archived paths in `generated_artifacts`.
7. If gate/report-summary currently allows prose claims about missing artifacts, add a focused check or test.

Allowed source/test changes only if needed:

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

Allowed project_state outputs:

- `project_state/state_rebuild_apply_plan.json`
- `project_state/proposed_state/artifact_index.json`
- `project_state/proposed_state/current_state.json`
- `project_state/proposed_state/negative_results.json`
- `project_state/proposed_state/model_gate.json`
- `project_state/proposed_state/task_packet.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260619_staged_state_artifact_closeout_v1/*`

## 7. Tests

Run and record all commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_state rebuild-stage --state-dir project_state --out-dir project_state/proposed_state
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If `gate-profile` says closeout is allowed:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_staged_state_artifact_closeout_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If source files are changed, run the relevant expanded gate/project-state tests required by the command plan.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` if:

1. staged artifacts are generated but not included in report/gate evidence;
2. apply-plan is missing;
3. proposed state files are missing;
4. live root state files are mutated accidentally;
5. decision-lint fails;
6. pytest fails;
7. final-check has any FAIL;
8. report/decision/pytest/final-gate IDs mismatch;
9. implementation weakens decision-lint or reverse-solving gate behavior;
10. report claims staged artifacts that cannot be found or archived;
11. source changes exceed allowed project-state/gate files;
12. report claims affine or samplereverse solving progress.

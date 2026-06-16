```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_target_revalidation_closeout_rework_v1",
  "round_id": "round_20260616_cpp1_target_revalidation_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out `round_20260616_cpp1_target_bytes_current_revalidation_v2` by reconciling report-summary, final-check, pytest_result, and round archive status.

The target bytes revalidation itself succeeded and must not be repeated unless required only for verification. This round is an engineering closeout/reconciliation round, not a reverse-solving round.

Required end state:

- `codex_report_summary` matches `report_summary_synthesis.json`.
- `final_gate_result.json` is not FAILED, or the live report honestly says FAILED / REWORK_REQUIRED.
- `close-round` exits 0.
- Archived report, decision, and pytest_result match live files.
- Current artifact `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` remains registered as current.

## 2. Current Evidence

The current execution authority is this `project_state/decision_packet.md`; `task_packet.json` remains state input only and must not override this decision.

The previous round was `round_20260616_cpp1_target_bytes_current_revalidation_v2`.

Known facts from the audit:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json` was generated.
- `project_state/artifact_index.json` registers `local_reverse_cpp1_2f6fcb63_target_bytes_revalidation` with `freshness=current`, `sample_id=cpp1_2f6fcb63`, and source_run `round_20260616_cpp1_target_bytes_current_revalidation_v2`.
- The revalidation command exited 0 and reported `status=PASSED`.
- No sample execution occurred.
- No candidate/password/flag was produced.
- `close-round` failed with exit 1.
- `final_gate_result.json` is FAILED because `status_policy_valid` blocks on 50 historical missing artifacts.
- `report_summary_synthesis.json` expects `FAILED / REWORK_REQUIRED`.
- `codex_execution_report.md` is internally inconsistent: the summary says `PARTIAL / REWORK_REQUIRED`, but the body still claims the full gate pipeline succeeded and close-round closed.

This is not a reverse-solving round. It is an `engineering_branch` closeout round for report/gate/archive consistency.

Historical missing artifacts must not be treated as current evidence. However, a missing or stale current artifact must still block.

Existing relevant capabilities:

- `project_gate.py` and `project_state.py` already implement gate/status/report policy checks.
- The previous engineering closeout strategy used `engineering_branch` to downgrade historical missing artifacts into external-state notices while keeping current artifacts strict.
- `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
- IDA/static extraction capability already exists, but it is not in scope for this closeout.
- Harness/runtime validation exists, but it is not in scope for this closeout.

## 3. Do Not Do

Do not rerun solver, brute force, harness campaign, debugger, emulator, runtime validation, or sample execution.

Do not rerun target bytes revalidation unless needed only to verify artifact presence and metadata.

Do not delete, downgrade, or alter the meaning of `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`.

Do not remove historical missing artifact entries just to pass the gate.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, or complete `solve_reports/`.

Do not modify `project_gate.py` or `project_state.py` unless the existing engineering closeout path cannot safely distinguish historical missing artifacts from current artifacts.

Do not widen this into frontend/backend work.

Do not generate candidate/password/flag.

Do not treat `task_packet.task` or old `samplereverse` state as the current execution task.

## 4. Files To Inspect

Read the default project_state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260616_cpp1_target_bytes_current_revalidation_v2/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- related gate/state tests if any source file is touched

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. Current decision id is `decision_20260616_cpp1_target_revalidation_closeout_rework_v1`.
3. Current mainline is `engineering_branch`.
4. `reverse-agent-iteration@v2` is active.
5. Current revalidation artifact exists and is current in `artifact_index.json`.
6. Previous close-round failed due to `status_policy_valid`.
7. The 50 missing artifacts are historical external state notices, not current required artifacts for `cpp1_2f6fcb63_target_bytes_revalidation`.
8. Current required artifact missing/stale must still block.
9. Live report, report-summary, final-check, and archive must describe the same status.

Required result:

- `codex_execution_report.md` must not claim SUCCESS if close-round fails.
- `codex_report_summary` must match `report_summary_synthesis.json`.
- `pytest_result.txt` must record real commands, stdout, stderr, and exit codes.
- `close-round` must exit 0 before reporting SUCCESS/ACCEPTED.

## 6. Implementation Scope

Prefer no source changes.

Allowed project_state updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260616_cpp1_target_revalidation_closeout_rework_v1/*`

Carefully allowed only if required:

- `project_state/artifact_index.json`, only for provenance/status metadata and not to change evidence meaning.

Only if existing engineering closeout cannot pass safely, allow minimal source changes to:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- directly related tests

Any source change must preserve the rule: current artifact missing/stale is blocking; historical missing artifacts may be downgraded only in this closeout-style engineering context.

Do not modify solver logic, harness runtime behavior, IDA runner semantics, sample-specific solver profiles, GUI/frontend, or `.codex-skills/`.

## 7. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

Required commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_target_revalidation_closeout_rework_v1
```

If source files are modified, run the directly relevant focused tests plus:

```powershell
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
```

## 8. Stop Conditions

Stop with `BLOCKED` if current revalidation artifact is missing or not current.

Stop with `REWORK_REQUIRED` if report-summary and live report still disagree.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `BLOCKED` if fixing this requires changing project_gate status policy outside this decision scope.

Stop with `REWORK_REQUIRED` if live `project_state/decision_packet.md` must be edited during Codex execution.

Do not write SUCCESS if close-round fails.

Do not write ACCEPTED if `pytest_result.txt` is missing, incomplete, or mismatched.

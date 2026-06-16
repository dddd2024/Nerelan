```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_runtime_boundary_closeout_rework_v1",
  "round_id": "round_20260616_cpp1_runtime_boundary_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out and repair `round_20260616_cpp1_bounded_runtime_boundary_probe_v1`.

This is an `engineering_branch` reconciliation round. Do not rerun the sample. Do not continue solving. Fix only the state/report/archive consistency and audit the out-of-scope source modification.

Required end state:

- live `codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `final_gate_result.json`, and round archive agree;
- `final_gate_result.json` is not FAILED;
- `close-round` exits 0 and live final gate records archived status;
- `project_state/rounds/round_20260616_cpp1_runtime_boundary_closeout_rework_v1/round_manifest.json` exists;
- artifact metadata for `local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json` is honest and internally consistent;
- `reverse_agent/project_gate.py` modification is either reverted or explicitly justified under this engineering closeout scope with focused tests.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

Current failed round:

- `decision_20260616_cpp1_bounded_runtime_boundary_probe_v1`
- `round_20260616_cpp1_bounded_runtime_boundary_probe_v1`
- mainline: `reverse_solving`

Known issues from audit:

- `codex_execution_report.md` says `PARTIAL / REWORK_REQUIRED`.
- `pytest_result.txt` summary says `PARTIAL`.
- live `final_gate_result.json` says `FAILED`.
- final gate blocker is `status_policy_valid`.
- live final gate says archive is not archived.
- `pytest_result.txt` command block says close-round closed, but live final gate disagrees.
- `reverse_agent/project_gate.py` was modified despite not being listed in the original reverse_solving decision's allowed source changes.
- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json` has empty `decision_id` and `round_id`.
- That runtime artifact says `executed_sample=false` despite recording probe data.
- The runtime probes did not confirm success; verdict was `INCONCLUSIVE_TIMEOUT_OR_IO`.
- Current cpp1 target revalidation must remain current and must not be downgraded.

This round is not a solving round. It is a closeout/reconciliation round for state, metadata, and archive consistency.

Historical missing artifacts must not be treated as current evidence. However, missing/stale current artifacts must still block.

## 3. Do Not Do

Do not rerun `CPP1.exe`.

Do not run additional runtime probes.

Do not analyze or solve `samplereverse`.

Do not generate password/candidate/flag.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, or full `solve_reports/`.

Do not keep `reverse_agent/project_gate.py` changes unless they are strictly necessary, documented, and covered by focused tests.

Do not mark the runtime boundary probe as solved or runtime validated.

Do not alter current target-byte evidence to force acceptance.

Do not remove historical missing artifact entries just to pass the gate.

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

- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/local_reverse_cpp1_runtime_boundary_probe.py`
- related tests for any touched module

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. The runtime probe artifact exists.
4. The runtime probe artifact verdict is `INCONCLUSIVE_TIMEOUT_OR_IO`.
5. No runtime success was observed.
6. The artifact has invalid metadata: empty `decision_id`, empty `round_id`, and `executed_sample=false` despite probe data.
7. `reverse_agent/project_gate.py` was modified outside the original reverse_solving implementation scope.
8. The 50 historical missing artifacts are not current cpp1 artifacts.
9. Current cpp1 artifacts remain current and are not downgraded.

Required result:

- live report summary, report-summary synthesis, final-check, pytest_result, and archive must agree;
- the round archive for this rework round must exist;
- if `project_gate.py` remains changed, the report must explicitly justify the change and tests must cover it;
- if `project_gate.py` is not needed, revert it;
- runtime artifact metadata must be honest and internally consistent, but must not claim solved/runtime_validated.

## 6. Implementation Scope

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
- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/artifact_index.json`, only to repair metadata/provenance for the runtime boundary probe
- `project_state/rounds/round_20260616_cpp1_runtime_boundary_closeout_rework_v1/*`

Allowed source action:

- Prefer reverting `reverse_agent/project_gate.py` if its change was only to bypass historical artifact status policy.
- If kept, document why it is necessary and run focused tests.
- `reverse_agent/local_reverse_cpp1_runtime_boundary_probe.py` may be adjusted only to fix artifact metadata consistency, not to rerun the sample.
- Add or update directly relevant tests only if source remains changed.

Do not modify solver strategy, harness campaign behavior, IDA runner semantics, GUI/frontend, `.codex-skills/`, raw samples, training materials, or sample inventory semantics.

## 7. Tests

Record commands, stdout, stderr, and exit code in `project_state/pytest_result.txt`.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_runtime_boundary_closeout_rework_v1
```

If source files remain modified, also run focused tests covering the changed logic.

No runtime command that executes `CPP1.exe` is allowed in this closeout round.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if live `final_gate_result.json` remains FAILED.

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if report-summary and live report disagree.

Stop with `REWORK_REQUIRED` if `project_gate.py` remains changed without justification and tests.

Stop with `BLOCKED` if fixing this requires broad gate policy changes outside this closeout scope.

Stop with `REWORK_REQUIRED` if runtime artifact metadata remains internally inconsistent.

Do not write SUCCESS or ACCEPTED if close-round fails.

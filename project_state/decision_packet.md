```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_static_triage_closeout_rework_v1",
  "round_id": "round_20260616_cpp1_static_triage_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out the previous `cpp1_2f6fcb63` static-triage round by fixing report/gate/archive consistency.

The previous round produced a useful static evidence artifact, but the live report and final gate disagree. This round is only a closeout/reconciliation round. Do not start a new sample and do not extend the analysis.

Required end state: report-summary, final-check, close-round, and round archive all describe the same status.

## 2. Current Evidence

The current execution authority is this `project_state/decision_packet.md`.

The previous round was `round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1`.

Current known facts:

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` exists.
- The artifact records static-only evidence and `runtime_validated=false`.
- The artifact source_run points to the previous round.
- The live report claims success with limitations.
- The final gate records failure because status policy still treats historical missing artifacts as blocking.
- Report summary synthesis expects `FAILED / REWORK_REQUIRED`, but live report says success.
- The previous round archive exists, but its manifest status follows the live report rather than the final gate synthesis.

Old `task_packet.json` and `current_state.json` still refer to historical `samplereverse` state. They are not the current task.

## 3. Do Not Do

Do not process a new sample.

Do not extend the static evidence.

Do not produce a candidate or mark the sample solved.

Do not remove historical missing artifact entries just to pass the gate.

Do not modify `.codex-skills/`, raw samples, training materials, or unrelated modules.

Do not modify live `project_state/decision_packet.md` during Codex execution.

Do not use `task_packet.task` as the current execution task.

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

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- related gate/state tests

## 5. Required Audit

Confirm before changing files:

1. Current decision id is `decision_20260616_cpp1_static_triage_closeout_rework_v1`.
2. Current mainline is `engineering_branch`.
3. `reverse-agent-iteration@v2` is active.
4. The previous static artifact exists and is the only sample-specific artifact in scope.
5. Historical missing artifacts are not current evidence for this closeout.
6. Current required artifacts must still remain strict: if the current static artifact is missing or stale, the round must fail.

## 6. Implementation Scope

Prefer no source changes. If code changes are necessary, keep them limited to:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed project_state updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260616_cpp1_static_triage_closeout_rework_v1/*`

Carefully allowed only if required:

- `project_state/artifact_index.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`

For those two files, only update provenance or limitation metadata. Do not change the meaning of existing evidence.

## 7. Acceptance Criteria

The round is acceptable only if:

1. `codex_report_summary` matches `report_summary_synthesis.json`.
2. `final_gate_result.json` is not FAILED, or the live report honestly says FAILED / REWORK_REQUIRED.
3. Historical missing artifacts do not block this engineering closeout.
4. A missing or stale current artifact still blocks.
5. The artifact index records the current artifact provenance clearly.
6. `close-round` exits 0.
7. The archived report, decision, and pytest result match the live files.

## 8. Tests

Record command, stdout, stderr, and exit code in `project_state/pytest_result.txt`:

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_static_triage_closeout_rework_v1
```

Test coverage must confirm:

1. historical missing artifacts can be downgraded for this closeout;
2. current artifact missing or stale remains blocking;
3. report-summary mismatch cannot be accepted;
4. artifact provenance is verifiable;
5. existing gate guards do not regress.

## 9. Stop Conditions

Stop and report `BLOCKED` if resolving the closeout requires new sample analysis.

Stop and report `BLOCKED` if historical and current artifact failures cannot be distinguished safely.

Stop and report `REWORK_REQUIRED` if live `decision_packet.md` must be edited during execution.

Do not write SUCCESS if command-plan, report-summary, final-check, or close-round fails.

Do not write SUCCESS if pytest_result is missing, incomplete, or mismatched.

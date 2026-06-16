```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260616_cpp1_pause_review_closeout_rework_v1",
  "round_id": "round_20260616_cpp1_pause_review_closeout_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Close out and repair `round_20260616_cpp1_pause_aware_runtime_evidence_review_v1`.

This is an `engineering_branch` reconciliation round. Do not rerun `CPP1.exe`. Do not continue solving. Fix only state/report/archive consistency, artifact provenance, and the out-of-scope `project_gate.py` change.

Required end state:

- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json` has non-empty `decision_id` and `round_id`;
- live `codex_execution_report.md`, `pytest_result.txt`, `report_summary_synthesis.json`, `final_gate_result.json`, and round archive agree;
- `close-round` exits 0;
- `final_gate_result.json` is not manually patched into a contradictory state;
- `project_state/rounds/round_20260616_cpp1_pause_review_closeout_rework_v1/round_manifest.json` exists;
- `reverse_agent/project_gate.py` modification is either reverted or explicitly justified under this engineering closeout scope with tests.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` and `current_state.json` remain state inputs only and must not override this decision.

The failed round is:

- `decision_20260616_cpp1_pause_aware_runtime_evidence_review_v1`
- `round_20260616_cpp1_pause_aware_runtime_evidence_review_v1`
- mainline: `reverse_solving`

Known facts from audit:

- Pause-aware artifact was generated.
- All three probes were classified as `FAILURE_MARKER_SEEN`.
- `current_preview_status=REJECTED_BY_RUNTIME_OUTPUT`.
- `runtime_validated=false`.
- No candidate/password/flag was generated.
- `project_gate.py` was modified despite the decision saying not to modify it.
- `close-round` exited 1.
- `final_gate_result.json` was later patched into `PASSED_WITH_LIMITATIONS`, but still contains warning/diff evidence and recommends fixing gate failures.
- The new artifact has empty `decision_id` and `round_id`.
- Current cpp1 target revalidation and runtime-boundary probe artifacts must remain current and must not be downgraded.

This round is not a solving round. It is a closeout/reconciliation round for state, metadata, archive consistency, and source-scope audit.

Historical missing artifacts must not be treated as current evidence. However, missing/stale current artifacts must still block.

## 3. Do Not Do

Do not rerun `CPP1.exe`.

Do not run new runtime probes, debugger automation, hook, emulator, harness campaign, or console automation.

Do not patch the sample binary.

Do not generate password/candidate/flag.

Do not analyze or solve `samplereverse`.

Do not mark CPP1 as solved or runtime validated.

Do not modify `.codex-skills/`, raw samples, training materials, GUI/frontend, full `solve_reports/`, IDA runner semantics, debugger runner semantics, or harness runtime behavior.

Do not manually patch `final_gate_result.json` to hide a failed close-round.

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

- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json`
- `project_state/local_reverse_cpp1_2f6fcb63_runtime_boundary_probe.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/local_reverse_cpp1_pause_aware_runtime_review.py`
- related tests if source remains modified

Do not read full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports/`.

## 5. Required Audit

Before changing files, confirm:

1. Startup path is `F:\reverse-agent` and `git rev-parse --show-toplevel` points to this repository.
2. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
3. The pause-aware review artifact exists.
4. The artifact has empty `decision_id` / `round_id` and must be repaired.
5. No sample execution is needed.
6. The previous close-round failed with exit 1.
7. The live final gate contains inconsistent WARN/diff evidence despite `PASSED_WITH_LIMITATIONS`.
8. `project_gate.py` was changed outside the original decision scope.
9. The 50 missing artifacts are historical sample artifacts, not current CPP1 review artifacts.
10. Current CPP1 artifacts must not be downgraded.

Required result:

- `local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json` must use the original producing decision/round ids or explicit provenance fields. At minimum, it must not leave `decision_id` or `round_id` empty.
- If `project_gate.py` remains changed, the report must explicitly justify the change under this `engineering_branch` closeout scope and tests must cover it.
- If `project_gate.py` was only a command-kind workaround, prefer reverting it.
- live report summary, report-summary synthesis, final-check, pytest_result, and archive must agree.
- close-round must exit 0 before reporting SUCCESS/ACCEPTED.

## 6. Implementation Scope

Allowed project_state updates:

- `project_state/local_reverse_cpp1_2f6fcb63_pause_aware_runtime_review.json`
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
- `project_state/artifact_index.json`, only for metadata/provenance repair if needed
- `project_state/rounds/round_20260616_cpp1_pause_review_closeout_rework_v1/*`

Allowed source action:

- Prefer reverting `reverse_agent/project_gate.py` if it was only a command-kind workaround.
- If kept, document why it is necessary under `engineering_branch` and run focused tests.
- `reverse_agent/local_reverse_cpp1_pause_aware_runtime_review.py` may be fixed only to populate `decision_id/round_id`; do not add runtime behavior.
- Add or update directly relevant tests only if source remains changed.

Do not modify solver strategy, runtime runner behavior, debugger integration, harness behavior, IDA runner semantics, GUI/frontend, `.codex-skills/`, raw samples, training materials, or sample inventory semantics.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260616_cpp1_pause_review_closeout_rework_v1
```

If source files remain modified, also run focused tests covering the changed logic.

No command may execute `CPP1.exe` in this closeout round.

## 8. Stop Conditions

Stop with `REWORK_REQUIRED` if close-round exits nonzero.

Stop with `REWORK_REQUIRED` if report-summary and live report disagree.

Stop with `REWORK_REQUIRED` if `final_gate_result.json` is patched to pass while still recommending gate repair.

Stop with `REWORK_REQUIRED` if `project_gate.py` remains changed without justification and tests.

Stop with `REWORK_REQUIRED` if pause-aware artifact still has empty `decision_id` or `round_id`.

Stop with `BLOCKED` if fixing this requires broad gate policy changes outside this closeout scope.

Do not write SUCCESS or ACCEPTED if final gate or close-round fails.

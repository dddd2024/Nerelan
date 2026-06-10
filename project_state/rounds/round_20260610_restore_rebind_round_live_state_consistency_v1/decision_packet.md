```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_restore_rebind_round_live_state_consistency_v1","round_id":"round_20260610_restore_rebind_round_live_state_consistency_v1","based_on_state_build_id":"state_20260610_060844_d17fc0ba1c82","based_on_state_digest":"d17fc0ba1c823d328028914b3a019555162b7da63b9b03972bd4d555c8bae215","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Restore live `project_state` consistency after the rebind round.

Do not create another broad chain of repair decisions. This round is only to make live `project_state/decision_packet.md`, `codex_execution_report.md`, `pytest_result.txt`, `model_gate.json`, and the current round archive mutually consistent.

This is an `engineering_branch` state/report consistency repair round. Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` remains advisory only.

## 2. Current Evidence

- Current selected state build is `state_20260610_060844_d17fc0ba1c82` with digest `d17fc0ba1c823d328028914b3a019555162b7da63b9b03972bd4d555c8bae215`.
- Active live decision before this restore round was `decision_20260610_rebind_unactionable_gate_repair_live_state_v1`.
- Live `codex_execution_report.md` still points to `decision_20260610_repair_report_archive_and_status_evidence_v1` instead of the active live decision.
- Live `pytest_result.txt` still points to `decision_20260610_repair_report_archive_and_status_evidence_v1` instead of the active live decision.
- Live `model_gate.json` still has `next_local_action: inspect_failed_case_result` even though `harness_diagnostics.case_results_missing == true`.
- `reverse_agent/project_state.py` already maps missing `case_results/` to `repair_harness_artifact`; source logic likely does not need further modification.
- A rebind round archive exists at `project_state/rounds/round_20260610_rebind_unactionable_gate_repair_live_state_v1/`, but its pytest record includes stale pre-archive outputs and does not prove live state consistency.
- The archived rebind pytest output recorded `lint-decision: FAILED` because `based_on_state_digest` no longer matched regenerated `current_state.state_digest`.
- The archived rebind pytest output also recorded `round_manifest_present: False` / `archive_status: not_archived` before the manifest existed, so archive and live-state evidence were not captured in final consistent order.
- `artifact_index.json` still contains stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, repeated stale probes, and stale hook reuse.
- Existing relevant capability is `reverse_agent/project_state.py` plus `tests/test_project_state.py` and harness artifact manifest tests. Do not duplicate state builder, harness, IDA/Ghidra/debugger, or solver interfaces.

## 3. Do Not Do

- Do not run any sample binary.
- Do not run solver/search/candidate generation/candidate validation.
- Do not run runtime probe, debugger, emulator, hook, sidecar, IDA, Ghidra, OllyDbg, or x64dbg.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not create another functional project-state feature.
- Do not hand-edit reverse-solving conclusions.
- Do not promote stale/missing artifacts to current.
- Do not solve the `samplereverse` sample in this round.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `project_state/rounds/round_20260610_rebind_unactionable_gate_repair_live_state_v1/round_manifest.json`
- `project_state/rounds/round_20260610_rebind_unactionable_gate_repair_live_state_v1/codex_execution_report.md`
- `project_state/rounds/round_20260610_rebind_unactionable_gate_repair_live_state_v1/pytest_result.txt`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm active live decision/report/pytest mismatch before changes.
2. Confirm this decision packet is based on `state_20260610_060844_d17fc0ba1c82` and digest `d17fc0ba1c823d328028914b3a019555162b7da63b9b03972bd4d555c8bae215`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm both skill profiles are active in `.codex-skills/registry.json`.
5. Confirm `task_packet.json` is advisory only and this decision controls the round.
6. Run `python -m reverse_agent.project_state build` using existing project-state tooling.
7. Confirm live `model_gate.json` now has `next_local_action: repair_harness_artifact` when `harness_diagnostics.case_results_missing == true`.
8. Update live `project_state/codex_execution_report.md` so it matches this restore decision.
9. Update live `project_state/pytest_result.txt` so it matches this restore report and includes exact command outputs.
10. Run final `lint-decision`, `lint-report`, and `status` after the live report/test files are updated.
11. Ensure final status shows:
    - `decision_report_id_match: True`
    - `decision_consumed_by_report: True`
    - `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`
    - `round_manifest_present: True`
    - `archive_status: archived`
12. Archive this restore round only after live report/test consistency is established.
13. After archive, rerun or record a final `lint-report` and `status` that reflect the archived restore round, not a pre-archive state.
14. Do not change source code unless tests prove the existing `repair_harness_artifact` branch is broken.
15. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
16. Ensure no sample/tool/debugger/solver/probe execution occurred.
17. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `tests/test_project_state.py`, only if a targeted regression assertion is missing
2. `reverse_agent/project_state.py`, only if a focused test proves the existing `repair_harness_artifact` branch is broken
3. `tests/test_harness_artifact_manifest.py`, only if directly affected

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/model_gate.json`, only via `python -m reverse_agent.project_state build`
4. `project_state/current_state.json`, `project_state/task_packet.json`, and `project_state/artifact_index.json`, only via build tooling
5. `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`

## 7. Tests

Run and record exact outputs in live `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

After archiving this restore round, record final outputs for:

```bash
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- `lint-decision: OK` for this restore decision, or an explicit report explanation if state rebuild changes digest before final report and the final consumed-report state is otherwise coherent.
- `lint-report: OK` after report update.
- pytest passes for all tests run.
- Live `model_gate.json` has `next_local_action: repair_harness_artifact` when `case_results_missing: true`.
- Live `codex_execution_report.md` matches this restore decision.
- Live `pytest_result.txt` matches this restore report.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True`.
- Final status shows `archive_status: archived`.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.
- Any source change is minimal, tested, and limited to project-state gate/report/build consistency.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Live `model_gate.json` cannot be regenerated to `repair_harness_artifact`.
- Live report/pytest cannot be made to match the active restore decision.
- Fixing requires sample execution or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation or validation.
- Fixing requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Fixing requires broad refactor outside project-state report/build/gate consistency.
- `.codex-skills/` changes are required.
- `lint-report` fails after the final report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```
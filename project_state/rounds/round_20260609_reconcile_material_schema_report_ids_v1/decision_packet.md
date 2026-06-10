```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_reconcile_material_schema_report_ids_v1","round_id":"round_20260609_reconcile_material_schema_report_ids_v1","based_on_state_build_id":"state_20260609_145049_7ee702d3b2b6","based_on_state_digest":"7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the report/pytest evidence mismatch from `decision_20260609_extend_material_evidence_schema_v1`.

The source changes for material evidence schema appear in-scope and should not be reverted. This round is only to reconcile `codex_execution_report.md`, `pytest_result.txt`, and round archive evidence so all IDs consistently reference the same active repair decision/round.

This is an `engineering_branch` repair round. It must not continue schema implementation, reverse solving, runtime probing, debugger work, or sample execution.

## 2. Current Evidence

- Previous implementation decision was `decision_20260609_extend_material_evidence_schema_v1`.
- Previous implementation report used `report_20260609_extend_material_evidence_schema_v1`.
- Previous `pytest_result.txt` summary used the extend-material IDs, but detailed lint outputs contained stale `decision_20260609_add_material_evidence_kinds_and_json_ingestion_v1` / `report_20260609_add_material_evidence_kinds_and_json_ingestion_v1` identifiers.
- Source changes appear limited to:
  - `reverse_agent/evidence.py`
  - `reverse_agent/tool_runners.py`
  - `tests/test_tool_runners.py`
- `reverse_agent/evidence.py` now contains material evidence constants/helpers for Base64/RC4/UTF-16LE material evidence.
- `reverse_agent/tool_runners.py` now contains `_ingest_material_evidence()` and extends `_structured_evidence_from_json()` to ingest explicit material fields.
- Tests appear to pass, but the recorded lint output is internally inconsistent, so the previous round cannot be accepted as-is.
- Current state is still based on `state_20260609_145049_7ee702d3b2b6` with digest `7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
- `task_packet.json` remains advisory only. This `decision_packet.md` controls the current round.
- `artifact_index.json` stale artifacts must remain stale and must not be promoted.
- `.codex-skills/registry.json` confirms `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.

## 3. Do Not Do

- Do not modify material evidence implementation unless a real test failure directly requires a minimal fix.
- Do not run samples or execute any sample binary.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, runtime probe, sidecar, winpty, console validator, or solver.
- Do not generate, mutate, rank, or validate candidates or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solving, or reverse-solving actions.
- Do not add duplicate tool runners.
- Do not modify `.codex-skills/`.
- Do not read or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not hand-edit reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`.
- Do not mark report `SUCCESS` unless final `lint-decision`, `lint-report`, and pytest all pass and no detailed output contains stale IDs.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/rounds/round_20260609_extend_material_evidence_schema_v1/round_manifest.json`
- `reverse_agent/evidence.py`
- `reverse_agent/tool_runners.py`
- `tests/test_tool_runners.py`
- `.codex-skills/registry.json`

Optional bounded files:

- `tests/test_project_state.py`
- `tests/test_ollydbg_preflight.py`
- `tests/test_pipeline.py`
- `tests/test_harness_artifact_manifest.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260609_145049_7ee702d3b2b6` and current state digest `7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
4. Confirm `task_packet.json` is advisory only.
5. Confirm material evidence source changes remain intact unless a real test failure requires a minimal fix.
6. Re-run the required lint and pytest commands and capture real outputs.
7. Ensure every detailed command output in `pytest_result.txt` uses only the current repair IDs:
   - `decision_20260609_reconcile_material_schema_report_ids_v1`
   - `report_20260609_reconcile_material_schema_report_ids_v1`
   - `round_20260609_reconcile_material_schema_report_ids_v1`
8. Ensure no stale `add_material_evidence_kinds_and_json_ingestion` identifiers remain in `pytest_result.txt` or `codex_execution_report.md`.
9. Update `codex_execution_report.md` for this repair round.
10. Update `pytest_result.txt` with this repair round's real outputs.
11. Confirm no sample/tool/debugger/solver/probe execution occurred.
12. Confirm no `.codex-skills/` changes occurred.
13. Archive this repair round using existing project-state archive tooling only after report/test consistency is achieved.

## 6. Implementation Scope

Allowed changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/rounds/round_20260609_reconcile_material_schema_report_ids_v1/round_manifest.json`, only if existing archive tooling is used.

Allowed only if tests fail and require minimal correction:

- `reverse_agent/evidence.py`
- `reverse_agent/tool_runners.py`
- `tests/test_tool_runners.py`

Disallowed changes:

- `.codex-skills/`
- new or duplicate tool runners
- solver/search/runtime/debugger execution code
- sample binaries
- sample metadata
- training status
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- hand-edited reverse-solving conclusions in dynamic state files

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_tool_runners.py tests/test_project_state.py -q
```

If broader compatibility is needed or if these files were already part of the material-schema compatibility suite, also run:

```bash
python -m pytest tests/test_ollydbg_preflight.py tests/test_pipeline.py tests/test_harness_artifact_manifest.py -q
```

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK`
- pytest passes
- no detailed command output contains stale `add_material_evidence_kinds_and_json_ingestion` identifiers
- `codex_execution_report.md` and `pytest_result.txt` IDs match this repair decision/round
- material schema source changes remain intact
- no sample execution, external reverse tool launch, runtime probe, solver/search, or full `solve_reports/` read occurred

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- `lint-decision` fails
- `lint-report` fails after report update
- pytest fails
- stale IDs remain in `pytest_result.txt` or `codex_execution_report.md`
- fixing requires external tools or sample execution
- fixing requires broad source refactor
- fixing requires `.codex-skills/` modification
- the task shifts from `engineering_branch` into `reverse_solving`, candidate generation, runtime validation, or debugger execution

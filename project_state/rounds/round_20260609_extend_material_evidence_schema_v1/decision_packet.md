```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_extend_material_evidence_schema_v1","round_id":"round_20260609_extend_material_evidence_schema_v1","based_on_state_build_id":"state_20260609_145049_7ee702d3b2b6","based_on_state_digest":"7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Implement the next bounded tool-integration step recommended by `project_state/tool_interface_gap_audit_material_evidence_v1.json`: extend structured evidence representation and JSON ingestion for Base64/RC4/UTF-16LE material evidence without adding duplicate tool runners or executing any external reverse-engineering tool.

The objective is to make material-probe JSON outputs representable as first-class `StructuredEvidence` records. This round is schema/converter/test work only. It must not run samples, run OllyDbg/IDA/Ghidra/x64dbg, launch runtime probes, generate candidates, or solve `samplereverse`.

## 2. Current Evidence

- Current state is consistent with `state_build_id=state_20260609_145049_7ee702d3b2b6` and `state_digest=7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
- The latest accepted `tool_integration` audit round is `round_20260609_tool_interface_gap_audit_for_material_evidence_v1`.
- The audit artifact `project_state/tool_interface_gap_audit_material_evidence_v1.json` concluded that existing IDA and OllyDbg interfaces should be reused rather than duplicated.
- The audit artifact identified these material evidence gaps:
  - no dedicated Base64 material evidence kind;
  - no dedicated RC4 material evidence kind;
  - no dedicated UTF-16LE constructor/material evidence kind;
  - material probe scripts exist, but their outputs are not unified in `_structured_evidence_from_json()`;
  - `CompareProbe` lacks instruction-level confirmation and should remain compare evidence, not material proof.
- `reverse_agent/evidence.py` currently defines a flexible `StructuredEvidence` dataclass with string `kind`, `source_tool`, `summary`, `payload`, optional `confidence`, and `derived_candidates`.
- `reverse_agent/tool_runners.py::_structured_evidence_from_json()` currently emits `CandidateEvidence`, `RuntimeCompareEvidence`, `StaticStringEvidence`, and `ConstraintEvidence`, but not Base64/RC4/UTF-16LE material evidence kinds.
- Existing `ToolAutomationConfig`, IDA runner, OllyDbg runner, and CompareProbe runner already exist in `reverse_agent/tool_runners.py`; this round must not create duplicate runners.
- `project_state/negative_results.json` forbids old blind search, beam/budget-only expansion, compare_semantics_agree=false primary frontier, full `solve_reports` commits, rerunning Base64/RC4 probes before instruction-level confirmation, and repeating producer/probe audits without using their classifications.
- `project_state/task_packet.json` remains advisory only. The execution authority is this `decision_packet.md`.
- `.codex-skills/registry.json` confirms `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.

## 3. Do Not Do

- Do not execute any sample binary.
- Do not run OllyDbg, x64dbg, IDA, Ghidra, Frida, radare2, objdump, debugger, emulator, hook, sidecar, winpty, runtime probe, or console validator.
- Do not generate, mutate, rank, or validate candidate inputs or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not rerun Base64/RC4 breakpoint probes.
- Do not introduce a duplicate IDA, OllyDbg, Ghidra, x64dbg, debugger, or tool-runner interface.
- Do not add Ghidra or x64dbg integration in this round.
- Do not inspect or commit full `solve_reports/`.
- Do not inspect full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not promote stale artifacts as current evidence.
- Do not mark OllyDbg/backend/runtime readiness as true.
- Do not hand-edit reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`.

## 4. Files To Inspect

Required project-state files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/tool_interface_gap_audit_material_evidence_v1.json`
- `.codex-skills/registry.json`

Required source/test files:

- `reverse_agent/evidence.py`
- `reverse_agent/tool_runners.py`
- `tests/test_tool_runners.py`
- `tests/test_project_state.py`

Optional bounded files, only if needed to keep behavior compatible:

- `tests/test_pipeline.py`
- `tests/test_harness_artifact_manifest.py`
- `tests/test_ollydbg_preflight.py`
- `reverse_agent/ollydbg_preflight.py`
- `docs/tooling/ollydbg_backend_setup.md`
- `reverse_agent/profiles/samplereverse.py`
- `reverse_agent/pipeline.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260609_145049_7ee702d3b2b6` and its digest matches `current_state.json`.
2. Confirm `decision_meta.mainline == tool_integration`.
3. Confirm both skill profiles are active:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
4. Confirm `task_packet.json` is advisory only and does not control this round.
5. Confirm stale artifacts remain stale and are not promoted as current evidence.
6. Inspect `project_state/tool_interface_gap_audit_material_evidence_v1.json` and use it as the direct scope anchor.
7. Extend evidence representation using the existing `StructuredEvidence` mechanism. Prefer adding explicit constants/helper constructors or documented kind strings rather than introducing a large inheritance hierarchy.
8. Update `_structured_evidence_from_json()` so it can ingest material-probe JSON shapes into these evidence kinds:
   - `Base64MaterialEvidence`
   - `RC4MaterialEvidence`
   - `UTF16LEMaterialEvidence`
9. Preserve existing behavior for `CandidateEvidence`, `RuntimeCompareEvidence`, `StaticStringEvidence`, and `ConstraintEvidence`.
10. Keep `CompareProbe` evidence as `RuntimeCompareEvidence` unless the JSON includes explicit instruction-level material fields. Do not treat compare capture alone as material proof.
11. Add unit tests using synthetic JSON dictionaries only. Tests must not call subprocesses, external tools, or sample binaries.
12. Ensure new tests cover at least:
   - Base64 material JSON ingestion;
   - RC4 KSA/PRGA material JSON ingestion;
   - UTF-16LE material JSON ingestion;
   - mixed JSON preserving existing candidate/compare/string/constraint evidence;
   - unknown or partial material fields handled without crashing.
13. Update `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` for this round.
14. If the implementation requires broad source refactoring, new external tool integration, or runtime execution, stop and report `BLOCKED` instead of widening scope.

## 6. Implementation Scope

Allowed source changes:

1. `reverse_agent/evidence.py`
   - Add lightweight material evidence kind constants/helpers if useful.
   - Keep existing `StructuredEvidence` dataclass compatible.
2. `reverse_agent/tool_runners.py`
   - Extend `_structured_evidence_from_json()` with material JSON ingestion branches.
   - Do not add new IDA/OllyDbg/Ghidra/x64dbg runners.
3. `tests/test_tool_runners.py`
   - Add focused synthetic tests for material evidence conversion.
4. Other tests only if necessary to preserve compatibility.

Allowed project-state/report changes:

1. `project_state/codex_execution_report.md`.
2. `project_state/pytest_result.txt`.
3. `project_state/rounds/round_20260609_extend_material_evidence_schema_v1/round_manifest.json`, only if existing archive tooling is used after report/test consistency is achieved.

Disallowed changes:

- `.codex-skills/`
- new duplicate tool runners
- solver/search/runtime/debugger execution code
- sample binaries
- sample metadata
- training status
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- hand-edited reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_tool_runners.py tests/test_project_state.py -q
```

If changes touch pipeline/harness/preflight compatibility, also run and record:

```bash
python -m pytest tests/test_pipeline.py tests/test_harness_artifact_manifest.py tests/test_ollydbg_preflight.py -q
```

Acceptance requirements:

- `lint-decision: OK`.
- `lint-report: OK` after this round's report is written.
- Relevant pytest subset passes.
- Existing evidence conversion behavior remains backward compatible.
- New material evidence conversion tests pass.
- No sample execution, external reverse tool launch, runtime probe, solver/search, or full `solve_reports/` read occurred.
- `codex_execution_report.md` and `pytest_result.txt` match this decision and round.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- `lint-decision` fails.
- `lint-report` fails after report update.
- pytest fails.
- evidence schema extension requires running external reverse tools or samples.
- implementation requires adding a duplicate IDA/OllyDbg/Ghidra/x64dbg runner.
- implementation requires modifying `.codex-skills/`.
- implementation requires reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- implementation requires hand-editing reverse-solving conclusions.
- the task shifts from `tool_integration` into `reverse_solving`, candidate generation, runtime validation, or debugger execution.

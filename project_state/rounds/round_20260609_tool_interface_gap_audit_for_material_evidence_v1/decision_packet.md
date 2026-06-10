```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_tool_interface_gap_audit_for_material_evidence_v1","round_id":"round_20260609_tool_interface_gap_audit_for_material_evidence_v1","based_on_state_build_id":"state_20260609_145049_7ee702d3b2b6","based_on_state_digest":"7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Perform a bounded tool-interface gap audit for the current material-evidence bottleneck, without running any external reverse-engineering tool or sample binary.

The immediate goal is to inspect existing reverse-agent interfaces for IDA/Ghidra/debugger/OllyDbg/tool-runner/StructuredEvidence support and determine the next safe integration step for recovering Base64/RC4 or UTF-16LE material evidence. This round must not solve the sample, run probes, generate candidates, or implement a duplicate tool interface.

## 2. Current Evidence

- Current state is post-build and consistent with `state_build_id=state_20260609_145049_7ee702d3b2b6` and `state_digest=7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
- The latest accepted reconciliation round aligned `decision_packet.md`, `codex_execution_report.md`, and `pytest_result.txt`; no further report repair is the main task.
- `project_state/current_state.json` remains a `samplereverse` sample-state context with `round_id=round_20260609_145049` and `workflow_status=REPORT_AVAILABLE`.
- `project_state/task_packet.json` remains advisory only. It carries `active_strategy=CompareAwareSearchStrategy` and `derived_task=collect_missing_evidence`, but must not override this decision packet.
- `project_state/current_state.json` indicates the current bottleneck is evidence collection rather than candidate search.
- Current summaries indicate Base64/RC4 material construction evidence is still missing or unresolved; compare-side or compare-producer evidence exists, but Base64/RC4/UTF-16LE material points are not yet current confirmed evidence.
- `project_state/artifact_index.json` was refreshed, but old reverse-solving artifacts remain stale or missing. Stale artifacts may be used only as leads, not current proof.
- `project_state/negative_results.json` blocks repeating old sample_solver blind search, beam/budget-only expansion, using compare_semantics_agree=false candidates as primary frontier, committing full `solve_reports/`, rerunning Base64/RC4 breakpoint probes before instruction-level confirmation, and repeating producer/probe audits without using their classifications.
- Existing repository search shows at least these relevant capabilities or precedents to inspect before adding anything new:
  - `reverse_agent/ollydbg_preflight.py`
  - `docs/tooling/ollydbg_backend_setup.md`
  - `tests/test_ollydbg_preflight.py`
  - `reverse_agent/evidence.py`
  - `reverse_agent/tool_runners.py`
  - `reverse_agent/profiles/samplereverse.py`
  - `reverse_agent/pipeline.py`
  - tests around tool runners, pipeline, harness artifact manifests, and project state
- `.codex-skills/registry.json` confirms `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.

## 3. Do Not Do

- Do not execute any sample binary.
- Do not run OllyDbg, x64dbg, IDA, Ghidra, Frida, radare2, objdump, debugger, emulator, hook, sidecar, winpty, runtime probe, or console validator.
- Do not generate, mutate, rank, or validate candidate inputs or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not rerun Base64/RC4 breakpoint probes.
- Do not repeat producer/probe audits without using their existing classifications.
- Do not inspect or commit full `solve_reports/`.
- Do not inspect full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not introduce a duplicate IDA/Ghidra/debugger/tool-runner interface if an existing interface already covers the need.
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
- `.codex-skills/registry.json`

Required source/test/tooling files:

- `reverse_agent/evidence.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/ollydbg_preflight.py`
- `reverse_agent/profiles/samplereverse.py`
- `reverse_agent/pipeline.py`
- `docs/tooling/ollydbg_backend_setup.md`
- `tests/test_tool_runners.py`
- `tests/test_ollydbg_preflight.py`
- `tests/test_pipeline.py`
- `tests/test_harness_artifact_manifest.py`
- `tests/test_project_state.py`

Optional bounded files, only if directly referenced by the required files:

- project-state generated static audit JSONs for cpp2 as interface precedents, but only to learn schema/provenance conventions, not as current samplereverse evidence.
- latest relevant `project_state/rounds/<round_id>/round_manifest.json` for recent accepted rounds.

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260609_145049_7ee702d3b2b6` and the digest matches `current_state.json`.
2. Confirm `decision_meta.mainline == tool_integration`.
3. Confirm both skill profiles are active:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
4. Confirm `task_packet.json` is advisory only and does not control this round.
5. Confirm stale artifacts remain stale and are not promoted as current evidence.
6. Inventory existing mature-tool integration points and classify each as `implemented`, `partial`, `preflight_only`, `schema_only`, `missing`, or `not_applicable`:
   - IDA / IDAPython
   - Ghidra
   - OllyDbg
   - x64dbg / debugger
   - strings / file / objdump / radare2
   - existing `tool_runners`
   - existing `StructuredEvidence` or equivalent evidence conversion
   - artifact registration / provenance / freshness handling
7. Map the current material-evidence bottleneck to existing interfaces. Specifically determine whether current code already has a way to ingest or represent:
   - instruction-confirmed Base64 construction points
   - instruction-confirmed RC4 KSA/PRGA points
   - UTF-16LE expansion or constructor evidence
   - compare-producer hooks as leads rather than solved evidence
8. Produce a bounded audit artifact under `project_state/`, for example `project_state/tool_interface_gap_audit_material_evidence_v1.json`, containing:
   - `schema_version`
   - `based_on_decision_id`
   - `based_on_state_build_id`
   - `based_on_state_digest`
   - `mainline`
   - inspected files
   - existing capabilities found
   - gaps found
   - duplicate-interface risks
   - recommended next decision type
   - explicit `no_external_tools_run=true`
   - explicit `stale_artifacts_promoted=false`
9. Update `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` for this round.
10. Do not modify source code unless the audit cannot be represented without a small schema/reporting helper. If source changes appear necessary, stop and report `BLOCKED` rather than widening scope.

## 6. Implementation Scope

Allowed changes:

1. New bounded audit artifact: `project_state/tool_interface_gap_audit_material_evidence_v1.json`.
2. `project_state/artifact_index.json`, only if existing project-state conventions require registering the new audit artifact with explicit provenance and freshness.
3. `project_state/codex_execution_report.md`, updated for this round.
4. `project_state/pytest_result.txt`, updated with exact command outputs for this round.
5. `project_state/rounds/round_20260609_tool_interface_gap_audit_for_material_evidence_v1/round_manifest.json`, only if existing archive tooling is used after report/test consistency is achieved.

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/tool execution code
- sample binaries
- sample metadata
- training status
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- hand-edited reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`
- new duplicate tool runners for capabilities already present

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py tests/test_tool_runners.py tests/test_ollydbg_preflight.py tests/test_pipeline.py tests/test_harness_artifact_manifest.py -q
```

If source code is not changed and one of the listed tests is unavailable in the local checkout, record the actual error and run the closest existing project-state/tool-runner/preflight test subset. Do not invent test results.

Acceptance requirements:

- `lint-decision: OK`.
- `lint-report: OK` after this round's report is written.
- pytest passes for the relevant project-state/tool-interface test subset.
- The audit artifact exists and is bounded.
- The audit artifact states no external reverse tools or samples were run.
- The audit artifact does not promote stale artifacts to current evidence.
- The report/pytest_result IDs match this decision and round.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- Existing tool interfaces cannot be safely audited without running external tools.
- The audit requires executing samples, solvers, debuggers, runtime probes, or external reverse tools.
- The audit requires reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- The audit requires modifying `.codex-skills/`.
- The audit requires implementing a new duplicate IDA/Ghidra/debugger interface.
- `lint-decision` fails.
- `lint-report` fails after this round's report is written.
- pytest fails and the failure is not an explicitly documented unavailable-test issue.
- `pytest_result.txt` cannot be updated with real outputs.
- The task shifts from `tool_integration` into `reverse_solving`, candidate generation, or runtime validation.

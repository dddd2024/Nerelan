```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_audit_existing_single_step_tool_interfaces_v1","round_id":"round_20260609_audit_existing_single_step_tool_interfaces_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Audit whether reverse-agent already has reusable interfaces for single-step debugging, breakpoint management, register/eflags/EIP reads, exception capture, and IDA/Ghidra/x64dbg/OllyDbg/Frida integration. The goal is to decide whether the next `samplereverse` evidence-producing round should reuse an existing tool interface or define a minimal single-step adapter.

This round is a `tool_integration` audit/design round only. It must not run samples, launch debuggers, run IDA/Ghidra, run Frida/OllyDbg/x64dbg, execute sidecars, run runtime probes, generate candidates, or modify solver/runtime code.

## 2. Current Evidence

- The previous accepted reverse-solving schema repair selected `needs_new_bounded_runtime_probe_decision` as the next recommendation category.
- The root capability gap is `step_api_unavailable`: the project cannot currently observe post-entry branch/eflags/next-EIP behavior inside the `0x401b50` handoff helper.
- `current_state.json` still records the `samplereverse` bottleneck as `window_lifecycle_no_window_created`, with stage `compare_handoff_narrower_post_entry_breakpoint_audit`.
- Current artifacts are indexed under `sr_arg0_hook_readiness_ordering_20260526_r1`, but this round must not read full `solve_reports/`; only bounded references needed to understand tool-interface requirements are allowed.
- `negative_results.json` prohibits returning to old `sample_solver` blind search, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports/`, and repeating several blocked Base64/RC4/material-hook directions.
- Existing relevant capabilities may include project-state tooling, compare-aware strategy code, harness-generated runtime artifacts, OllyDbg scripts, debugger wrappers, Frida helpers, and possible IDA/Ghidra extraction interfaces. This round must verify these from repository code instead of assuming they do or do not exist.
- Mature reverse tools should be reused when available. If IDA/Ghidra/x64dbg/OllyDbg already provide the needed evidence extraction, the next round should propose using that interface instead of reimplementing debugger functionality.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.

## 3. Do Not Do

- Do not execute any sample binary, including `samplereverse` or `Cpp2.exe`.
- Do not launch IDA, Ghidra, OllyDbg, x64dbg, Frida, debugger, emulator, runtime probe, hook, sidecar, winpty, console validator, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run compare-aware search, old `sample_solver` blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any solver action.
- Do not implement a single-step adapter in this round.
- Do not modify source modules.
- Do not modify `.codex-skills/`.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify training status, sample metadata, status overlay, archive directories, runtime artifacts, artifact freshness, or solver code.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not promote stale or unknown-freshness artifacts to current evidence.

## 4. Files To Inspect

Required project-state files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `project_state/task_packet.json`

Required repository search terms and bounded inspection targets:

- `step`, `single_step`, `single-step`
- `Frida`, `frida`
- `x64dbg`
- `OllyDbg`, `olly`
- `debugger`, `breakpoint`, `register`, `eflags`, `eip`
- `IDA`, `idapython`, `Ghidra`
- `compare_handoff_post_entry_step_audit.py`, if present
- existing scripts under `reverse_agent/olly_scripts/`, if present
- existing tool integration modules under `reverse_agent/` that expose debugger/static-tool functionality

Optional bounded source/test inspection, only to determine existing interface shape:

- tests that mention debugger, Frida, OllyDbg, x64dbg, IDA, Ghidra, breakpoint, register, eflags, or EIP
- README/tooling docs that describe supported reverse tools

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == tool_integration`.
4. Confirm both skill profiles resolve to active registry skills:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm no sample execution, runtime probing, debugger/emulator launch, IDA/Ghidra launch, sidecar execution, solver work, or candidate validation occurred.
7. Inventory existing interfaces for:
   - single-step execution
   - breakpoint install/remove/list
   - register read/write
   - EFLAGS/EIP/next-EIP observation
   - exception capture/access-violation capture
   - IDA/IDAPython static extraction
   - Ghidra static extraction
   - x64dbg/OllyDbg integration
   - Frida integration
   - StructuredEvidence conversion from tool output
8. Explain why `compare_handoff_post_entry_step_audit.py` or equivalent currently reports `step_api_unavailable`, if the script or prior report exists in repository state.
9. Distinguish mature tool capabilities from project wrapper capabilities: note whether a mature tool can do the work manually, and whether reverse-agent already has a wrapper to orchestrate it.
10. Identify which existing interface, if any, should be reused for the next evidence-producing round.
11. If no reusable interface exists, define the minimal single-step adapter boundary without implementing it. The boundary must include inputs, outputs, tool backend, safety limits, provenance/artifact output, and stop conditions.
12. Cross-check `negative_results.json`; explicitly state that this interface audit does not repeat blocked solver/probe directions.
13. Produce one final recommendation category, exactly one of:
    - `reuse_existing_debugger_step_interface`
    - `reuse_existing_static_tool_interface`
    - `need_minimal_single_step_adapter`
    - `need_manual_ida_x64dbg_decision`
    - `blocked_no_interface_evidence`
14. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
15. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes:

1. `project_state/codex_execution_report.md`, updated with the interface inventory, existing capability matrix, negative-results cross-check, and final recommendation category.
2. `project_state/pytest_result.txt`, updated with this round's command outputs.
3. Optional compact JSON artifact: `project_state/single_step_tool_interface_audit_20260609.json`, if Codex needs machine-readable output. If created, list it in `generated_artifacts` and keep it small.

Disallowed changes:

- source modules
- `.codex-skills/`
- solver code
- runtime probe code
- sample metadata
- training status
- status overlay
- artifact freshness
- archive directories
- full `solve_reports/`

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

If the optional JSON artifact is created, also run and record:

```bash
python -m json.tool project_state/single_step_tool_interface_audit_20260609.json > NUL
```

Use the platform-appropriate null sink if not on Windows, and record the actual command used.

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK`
- `pytest tests/test_project_state.py` passes
- optional JSON validates if created
- report/test IDs match this decision and round
- report includes the interface inventory
- report includes exactly one final recommendation category from the allowed list
- no sample execution, debugger/emulator launch, IDA/Ghidra launch, Frida/OllyDbg/x64dbg run, sidecar execution, solver work, candidate validation, source modification, or full `solve_reports/` inspection occurred

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if any of the following occurs:

- determining interface capability requires launching a debugger, IDA/Ghidra, Frida, x64dbg, OllyDbg, sidecar, or sample binary
- determining interface capability requires full `solve_reports/` scanning
- repository search cannot determine whether a relevant wrapper exists
- final recommendation cannot be reduced to exactly one allowed category
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- `pytest_result.txt` cannot be updated with real outputs from this round
- report/test IDs mismatch
- any task shifts this round into reverse execution, solver work, sample solving, or training dataset work

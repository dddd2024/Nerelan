```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_single_step_interface_audit_category_v1","round_id":"round_20260609_fix_single_step_interface_audit_category_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the single-step tool-interface audit report category. The current report uses an invalid final recommendation category, `needs_manual_ida_or_x64dbg_tool_integration_decision`. Replace it with exactly one category allowed by the active decision, and make the report conclusion consistent with that category.

This is a `tool_integration` report-schema repair round only. Do not rerun interface discovery unless needed to preserve already recorded wording. Do not run samples, debuggers, IDA/Ghidra, Frida, OllyDbg, x64dbg, sidecars, runtime probes, solvers, or candidate validation.

## 2. Current Evidence

- Current report is `report_20260609_audit_existing_single_step_tool_interfaces_v1`.
- The report/test IDs match the current decision/round and lint/pytest passed.
- The report says existing OllyDbg single-step infrastructure exists and should be reused.
- The report also says the backend is not configured.
- The report uses invalid category `needs_manual_ida_or_x64dbg_tool_integration_decision`.
- The governing decision only allowed:
  - `reuse_existing_debugger_step_interface`
  - `reuse_existing_static_tool_interface`
  - `need_minimal_single_step_adapter`
  - `need_manual_ida_x64dbg_decision`
  - `blocked_no_interface_evidence`
- If preserving the current “reuse existing OllyDbg infrastructure” conclusion, the likely corrected category is `reuse_existing_debugger_step_interface`.
- If Codex instead concludes a human/tool-selection decision is still required, use the exact allowed category `need_manual_ida_x64dbg_decision`, not a newly invented variant.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits; this repair round must not execute any of those directions.

## 3. Do Not Do

- Do not execute any sample binary.
- Do not launch IDA, Ghidra, OllyDbg, x64dbg, Frida, debugger, emulator, sidecar, runtime probe, hook, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs.
- Do not run solvers or compare-aware search.
- Do not implement or modify any adapter.
- Do not modify source modules.
- Do not modify `.codex-skills/`.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify artifact freshness, training status, sample metadata, archive directories, status overlay, runtime artifacts, or solver code.
- Do not treat `task_packet.task` or `derived_task` as execution authority.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

Optional bounded:

- `project_state/current_state.json`
- `project_state/artifact_index.json`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == tool_integration`.
4. Confirm both profiles are active:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Replace invalid `needs_manual_ida_or_x64dbg_tool_integration_decision` with exactly one allowed category:
   - `reuse_existing_debugger_step_interface`
   - `reuse_existing_static_tool_interface`
   - `need_minimal_single_step_adapter`
   - `need_manual_ida_x64dbg_decision`
   - `blocked_no_interface_evidence`
7. Ensure `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` use the same corrected category.
8. Ensure report conclusion and selected category are consistent.
9. Confirm no runtime/debugger/tool/sample execution occurred.
10. Confirm no source, skill, artifact, archive, training, status overlay, or runtime changes occurred.
11. Confirm stale artifacts remain stale and are not promoted as current evidence.
12. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
13. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes only:

1. `project_state/codex_execution_report.md`, updated to correct the final recommendation category and align the conclusion with that category.
2. `project_state/pytest_result.txt`, updated with this round's command outputs and the corrected matching recommendation category.

No source changes. No artifact changes. No optional JSON needed unless existing tooling requires it.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Acceptance requires:

- `lint-decision: OK`
- `lint-report: OK`
- pytest passes
- report/test IDs match this decision/round
- final recommendation category is exactly one allowed value
- report and `pytest_result.txt` category match
- report conclusion and selected category are consistent
- no reverse/tool execution occurred

## 8. Stop Conditions

Stop and report `FAILED` if any of the following occurs:

- final category is still outside the allowed list
- report and `pytest_result.txt` disagree on category
- report conclusion contradicts the selected category
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- any task requires running debugger, sample, sidecar, IDA/Ghidra, Frida, x64dbg, OllyDbg, or runtime probe
- any source, skill, artifact, archive, training status, status overlay, or runtime artifact modification becomes necessary

```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_single_step_audit_pytest_record_v1","round_id":"round_20260609_fix_single_step_audit_pytest_record_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the evidence record for the single-step interface audit category repair. The current `pytest_result.txt` top summary says it belongs to `decision_20260609_fix_single_step_interface_audit_category_v1`, but the recorded `status` and `lint-report` command outputs still contain old IDs from `decision_20260609_audit_existing_single_step_tool_interfaces_v1`.

This round must regenerate or correctly record final command outputs after the current report and pytest_result have been updated. Do not merely edit the summary block.

This is a `tool_integration` evidence-record repair round only. Do not run samples, debuggers, IDA/Ghidra, Frida, OllyDbg, x64dbg, sidecars, runtime probes, solvers, or candidate validation.

## 2. Current Evidence

- `codex_execution_report.md` now uses valid category `reuse_existing_debugger_step_interface`.
- The report conclusion and selected category are consistent.
- `pytest_result.txt` top summary uses the current repair IDs from `decision_20260609_fix_single_step_interface_audit_category_v1`.
- But the recorded `status` command output still reports old IDs from `decision_20260609_audit_existing_single_step_tool_interfaces_v1`.
- The recorded `lint-report` command output also still includes old `pytest_result_decision_id`, `pytest_result_report_id`, and `pytest_result_round_id` values from `decision_20260609_audit_existing_single_step_tool_interfaces_v1`.
- Therefore the current testing evidence is internally inconsistent and cannot be accepted.
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
- Do not only hand-edit the top summary of `pytest_result.txt` while leaving stale command outputs below.

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
6. Confirm `codex_execution_report.md` uses this decision ID and round ID.
7. Confirm `pytest_result.txt` does not contain stale previous-round IDs in any command output.
8. Regenerate or correctly record final command outputs after report/test updates.
9. Ensure `status`, `lint-decision`, `lint-report`, and pytest outputs all correspond to this round.
10. Ensure `pytest_result.txt` summary and command bodies agree.
11. Confirm no runtime/debugger/tool/sample execution occurred.
12. Confirm no source, skill, artifact, archive, training, status overlay, or runtime changes occurred.
13. Confirm stale artifacts remain stale and are not promoted as current evidence.
14. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
15. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes only:

1. `project_state/codex_execution_report.md`, updated for this evidence-record repair round.
2. `project_state/pytest_result.txt`, updated with real final command outputs for this round, with no stale previous-round IDs remaining.

No source changes. No artifact changes. No optional JSON needed.

## 7. Tests

Run and record final outputs after updating the report:

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
- all recorded command outputs reference `decision_20260609_fix_single_step_audit_pytest_record_v1`
- report/test IDs match this decision/round
- no stale previous-round IDs remain in `pytest_result.txt`
- `pytest_result.txt` summary and command bodies agree
- no reverse/tool execution occurred

## 8. Stop Conditions

Stop and report `FAILED` if any of the following occurs:

- final `pytest_result.txt` still contains stale old decision/report/round IDs
- report and `pytest_result.txt` disagree
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- any task requires running debugger, sample, sidecar, IDA/Ghidra, Frida, x64dbg, OllyDbg, or runtime probe
- any source, skill, artifact, archive, training status, status overlay, or runtime artifact modification becomes necessary

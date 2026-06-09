```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_ollydbg_preflight_validation_v1","round_id":"round_20260609_fix_ollydbg_preflight_validation_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the OllyDbg backend preflight implementation and evidence record. The previous round created `project_state/ollydbg_preflight_result.json` but did not record `python -m json.tool` validation. It also reports `sample_path_resolvable` but does not include it in the `ready` decision, which can incorrectly mark the backend ready when the sample path is missing.

This is a bounded `tool_integration` repair round. Do not launch OllyDbg, x64dbg, IDA/Ghidra, Frida, sidecars, debuggers, or samples.

## 2. Current Evidence

- `reverse_agent/ollydbg_preflight.py` exists and is non-invasive.
- `tests/test_ollydbg_preflight.py` exists and currently passes.
- `project_state/ollydbg_preflight_result.json` exists.
- `pytest_result.txt` records preflight generation but not JSON validation with `python -m json.tool`.
- `ready` currently ignores `sample_path_resolvable`.
- Some tests rely on the current environment not having OllyDbg/ollyscript configured.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits; this repair round must not execute any of those directions.

## 3. Do Not Do

- Do not execute samples.
- Do not launch OllyDbg, x64dbg, IDA, Ghidra, Frida, debugger, emulator, sidecar, hook, or runtime probe.
- Do not attach to any process.
- Do not run script injection.
- Do not run solvers, compare-aware search, or candidate validation.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify training status, sample metadata, archive directories, artifact freshness, status overlay, or runtime artifacts.
- Do not implement debugger functionality that OllyDbg/x64dbg already provides.
- Do not treat `task_packet.task` or `derived_task` as execution authority.

## 4. Files To Inspect

Required:

- `reverse_agent/ollydbg_preflight.py`
- `tests/test_ollydbg_preflight.py`
- `project_state/ollydbg_preflight_result.json`
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
6. Keep the preflight non-invasive: no external tool start, no attach, no sample execution, no sidecar, no runtime probe.
7. Include sample path readiness in the final runtime-readiness logic, or explicitly split readiness into `backend_ready` and `runtime_ready` so missing sample path cannot be confused with ready-to-run runtime probing.
8. Make tests hermetic by mocking environment variables, common path discovery, and module availability. Tests must not depend on whether the local machine has OllyDbg, `olly.ollyscript`, or sample files installed.
9. Validate `project_state/ollydbg_preflight_result.json` with `python -m json.tool` and record the command output/status in `pytest_result.txt`.
10. Confirm generated JSON, report summary, and pytest_result summary use the same recommendation.
11. Cross-check `negative_results.json`; state explicitly that this configuration/preflight work does not repeat blocked solver/probe directions.
12. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
13. Confirm no source, skill, artifact freshness, training, sample metadata, status overlay, archive, or runtime artifact changes occurred outside the allowed scope.
14. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.

## 6. Implementation Scope

Allowed changes:

1. `reverse_agent/ollydbg_preflight.py`, only to repair readiness semantics and keep the preflight non-invasive.
2. `tests/test_ollydbg_preflight.py`, only to make tests hermetic and cover missing sample-path readiness.
3. `project_state/ollydbg_preflight_result.json`, regenerated from the repaired preflight.
4. `project_state/codex_execution_report.md`, updated for this repair round.
5. `project_state/pytest_result.txt`, updated with real final command outputs for this round, including JSON validation.

No other source changes unless strictly necessary for imports.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py tests/test_ollydbg_preflight.py
python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json
python -m json.tool project_state/ollydbg_preflight_result.json > NUL
```

Use the platform-appropriate null sink if not on Windows, and record the actual command used.

Acceptance requires:

- `lint-decision: OK`
- `lint-report: OK`
- pytest passes
- JSON validates
- report/test IDs match this decision and round
- no stale old IDs in `pytest_result.txt`
- generated JSON, report summary, and pytest_result summary use the same recommendation
- no external reverse tool/sample execution
- missing sample path cannot produce runtime-ready status
- tests do not depend on real local OllyDbg/ollyscript/sample installation state

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- JSON validation is not recorded
- tests still depend on real local OllyDbg/ollyscript/sample installation state
- readiness still ignores sample path or fails to distinguish backend readiness from runtime readiness
- any external tool/sample execution becomes necessary
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- report/test IDs mismatch
- any broad refactor outside the bounded preflight module/test/report scope becomes necessary

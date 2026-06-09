```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_ollydbg_preflight_hermetic_tests_v1","round_id":"round_20260609_fix_ollydbg_preflight_hermetic_tests_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining non-hermetic tests in `tests/test_ollydbg_preflight.py`. The previous round fixed JSON validation and readiness semantics, but tests still depend on the local machine not having OllyDbg/ollyscript/sample configured.

This is a bounded `tool_integration` test repair round. Do not launch OllyDbg, x64dbg, IDA/Ghidra, Frida, sidecars, debuggers, or samples.

## 2. Current Evidence

- `ready`, `backend_ready`, and `runtime_ready` semantics are now correct.
- JSON validation is now recorded.
- `project_state/ollydbg_preflight_result.json` is valid and consistent.
- `test_olly_script_module_not_available_by_default` directly depends on local import state.
- `test_preflight_main_cli_exit_code` directly depends on local environment variables, common paths, and module availability.
- Report claims tests are hermetic, but the actual test file still contains real-environment assumptions.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits; this test repair round must not execute any of those directions.

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
- Do not modify readiness semantics except if a tiny change is required to make CLI testing deterministic.
- Do not treat `task_packet.task` or `derived_task` as execution authority.

## 4. Files To Inspect

Required:

- `tests/test_ollydbg_preflight.py`
- `reverse_agent/ollydbg_preflight.py`
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
6. Make `tests/test_ollydbg_preflight.py` fully hermetic.
7. Remove or rewrite `test_olly_script_module_not_available_by_default` so it mocks `importlib.util.find_spec` or `_olly_script_module_available`, instead of relying on local installed modules.
8. Rewrite the CLI test so it cannot be affected by local `REVERSE_AGENT_OLLYDBG_PATH`, `REVERSE_AGENT_SAMPLE_PATH`, common Windows paths, or installed Python modules. Acceptable options:
   - Prefer testing `main()` with mocked preflight dependencies; or
   - Run subprocess with sanitized environment and a deterministic test-only mode, if already supported; or
   - Avoid subprocess and test CLI argument plumbing through direct function calls.
9. Ensure no test depends on real local OllyDbg, `olly.ollyscript`, `ollyscript`, `OllyScript`, `olly`, or sample installation state.
10. Keep the preflight non-invasive: no external tool start, no attach, no sample execution, no sidecar, no runtime probe.
11. Preserve readiness semantics: missing sample path must not produce runtime-ready status.
12. Confirm generated JSON, report summary, and pytest_result summary use the same recommendation.
13. Cross-check `negative_results.json`; state explicitly that this test repair does not repeat blocked solver/probe directions.
14. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
15. Confirm no source, skill, artifact freshness, training, sample metadata, status overlay, archive, or runtime artifact changes occurred outside the allowed scope.
16. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.

## 6. Implementation Scope

Allowed changes:

1. `tests/test_ollydbg_preflight.py`, to make all tests hermetic and deterministic.
2. `reverse_agent/ollydbg_preflight.py`, only if needed to make CLI behavior testable without subprocess/environment dependence; keep changes minimal.
3. `project_state/ollydbg_preflight_result.json`, regenerated only if preflight output changes.
4. `project_state/codex_execution_report.md`, updated for this test repair round.
5. `project_state/pytest_result.txt`, updated with real final command outputs for this round.

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
- readiness semantics do not regress
- all preflight tests are hermetic and do not depend on real local OllyDbg/ollyscript/sample installation state

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- any test still relies on real local OllyDbg/ollyscript/sample installation state
- JSON validation is not recorded
- readiness semantics regress
- any external tool/sample execution becomes necessary
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- report/test IDs mismatch
- any broad refactor outside the bounded preflight module/test/report scope becomes necessary

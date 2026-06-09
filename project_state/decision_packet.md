```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_ollydbg_user_path_preflight_validation_v1","round_id":"round_20260609_ollydbg_user_path_preflight_validation_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Validate the user-provided OllyDbg tool location in the existing non-invasive preflight path.

The user provided the tool address as:

```text
E:\Program Files\ollydbg
```

This appears to be a directory, not necessarily the executable file. The current OllyDbg preflight contract says `REVERSE_AGENT_OLLYDBG_PATH` should point to `ollydbg.exe`, while the user supplied a directory. This round must ensure the preflight handles that safely and does not mark a directory as an executable. It may either:

1. resolve a directory path to `ollydbg.exe` inside that directory if present, for example `E:\Program Files\ollydbg\ollydbg.exe`; or
2. report a precise configuration error requiring the executable path.

This is still a bounded `tool_integration` preflight/configuration round. Do not launch OllyDbg, x64dbg, IDA/Ghidra, Frida, sidecars, debuggers, runtime probes, hooks, or samples.

## 2. Current Evidence

- The latest accepted round is `decision_20260609_fix_ollydbg_env_contract_recommendation_consistency_v1` / `round_20260609_fix_ollydbg_env_contract_recommendation_consistency_v1`.
- Actual preflight tool output uses `recommendation: preflight_not_configured_user_env_needed`.
- Workflow next step is `blocked_waiting_for_user_ollydbg_env_config` until the user configures the environment.
- User has now provided a concrete OllyDbg tool location: `E:\Program Files\ollydbg`.
- Existing setup docs say `REVERSE_AGENT_OLLYDBG_PATH` should be an absolute path to `ollydbg.exe`.
- Existing preflight must not confuse a directory path with an executable path.
- Existing `ready == runtime_ready`; runtime readiness still requires backend readiness and sample path readiness.
- The user has not provided a sample path in this message. Therefore this round must not assume `runtime_ready` can become true unless sample path is explicitly configured or already discoverable.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.
- `negative_results.json` continues to prohibit blind solver/search directions, only increasing beam/budget, `compare_semantics_agree=false` primary frontier, full `solve_reports/` commits, and repeated blocked Base64/RC4/material-hook directions.

## 3. Do Not Do

- Do not execute samples.
- Do not launch OllyDbg, x64dbg, IDA, Ghidra, Frida, debugger, emulator, sidecar, hook, or runtime probe.
- Do not attach to any process.
- Do not run script injection.
- Do not run solvers, compare-aware search, brute force, beam expansion, budget expansion, topN expansion, or candidate validation.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver code, compare-aware search logic, runtime probe code, training status, sample metadata, archive directories, artifact freshness, status overlay, or runtime artifacts.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not claim OllyDbg is usable merely because the directory exists.
- Do not proceed to runtime probing even if the executable path is found; this round is preflight/config validation only.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/ollydbg_preflight_result.json`
- `reverse_agent/ollydbg_preflight.py`
- `tests/test_ollydbg_preflight.py`
- `docs/tooling/ollydbg_backend_setup.md`
- `.env.example`
- `.codex-skills/registry.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

Optional bounded:

- Existing docs or config code that mention `REVERSE_AGENT_OLLYDBG_PATH`, executable path handling, or preflight status fields.

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
6. Inspect current `_ollydbg_exe_path()` behavior and determine whether it can misclassify a directory path as a found executable.
7. If the current behavior accepts any existing path, repair it so executable readiness requires a file path to an executable-like file, preferably named `ollydbg.exe` on Windows.
8. Add support for the user-provided directory path `E:\Program Files\ollydbg` by resolving it to `E:\Program Files\ollydbg\ollydbg.exe` if that file exists, or otherwise reporting a precise missing executable condition.
9. Keep tests hermetic. Add or update mocked tests for:
   - env var points directly to an executable file;
   - env var points to a directory containing `ollydbg.exe`;
   - env var points to a directory without `ollydbg.exe` and must not be marked executable-found;
   - env var points to a non-existent path;
   - runtime readiness remains false when sample path is missing, even if backend executable is found.
10. Rerun preflight non-invasively with `REVERSE_AGENT_OLLYDBG_PATH` set to the user-provided path or by passing an equivalent CLI/config value if supported. Record whether it resolves to an executable or remains blocked.
11. Preserve the distinction between `preflight_recommendation` and `next_decision_recommendation` in report and pytest summary.
12. Confirm generated JSON, report summary, and pytest_result summary agree on the actual preflight tool recommendation.
13. Cross-check `negative_results.json`; state explicitly that this path-validation work does not repeat blocked solver/probe directions.
14. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
15. Confirm no external reverse tool or sample was launched.
16. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.

## 6. Implementation Scope

Allowed changes:

1. `reverse_agent/ollydbg_preflight.py`, only to make OllyDbg executable path validation safe and support directory-to-`ollydbg.exe` resolution.
2. `tests/test_ollydbg_preflight.py`, only to add/update hermetic tests for path validation and directory resolution.
3. `docs/tooling/ollydbg_backend_setup.md`, only if wording must clarify directory vs executable path handling.
4. `.env.example`, only if the example should clarify that either the executable path or supported directory path may be provided.
5. `project_state/ollydbg_preflight_result.json`, regenerated only by running the existing non-invasive preflight command with the provided path context.
6. `project_state/codex_execution_report.md`, updated for this round.
7. `project_state/pytest_result.txt`, updated with real final command outputs for this round.

Disallowed changes:

- `.codex-skills/`
- solver code
- compare-aware search logic
- runtime probe logic
- sample metadata
- training status
- status overlay
- artifact freshness
- archive directories
- full `solve_reports/`
- any code that launches/drives OllyDbg/x64dbg/IDA/Ghidra/Frida

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py tests/test_ollydbg_preflight.py
```

Run the non-invasive preflight with the user-provided path context and record the actual command used. On Windows this may be:

```powershell
$env:REVERSE_AGENT_OLLYDBG_PATH = "E:\Program Files\ollydbg"
python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json
```

Then validate JSON and record the command:

```bash
python -m json.tool project_state/ollydbg_preflight_result.json > NUL
```

Use the platform-appropriate null sink if not on Windows.

Acceptance requires:

- `lint-decision: OK`
- `lint-report: OK`
- pytest passes
- JSON validates
- report/test IDs match this decision and round
- no stale old IDs in `pytest_result.txt`
- directory path handling cannot mark a directory as an executable
- if `E:\Program Files\ollydbg\ollydbg.exe` exists, preflight records the resolved executable path; otherwise it reports a missing executable while preserving `preflight_not_configured_user_env_needed`
- missing sample path cannot produce `runtime_ready=true`
- generated JSON, report summary, and pytest_result summary agree on the actual preflight recommendation
- any next-step recommendation is in a separate field and equals one of:
  - `blocked_waiting_for_user_sample_or_ollyscript_config`
  - `ready_for_bounded_ollydbg_runtime_decision_after_user_preflight`
  - `needs_ollydbg_path_validation_rework`
- no external reverse tool/sample execution occurred

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- validating the path requires launching OllyDbg, x64dbg, IDA/Ghidra, Frida, a sidecar, or a sample binary
- path validation still accepts a directory as an executable
- preflight behavior changes outside path validation/readiness reporting
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- JSON validation is not recorded
- report/test IDs mismatch
- any task shifts into sample solving, runtime probing, solver work, or external debugger/tool execution

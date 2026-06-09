```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_ollydbg_env_setup_contract_v1","round_id":"round_20260609_ollydbg_env_setup_contract_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Turn the accepted OllyDbg backend preflight result into a clear user-environment setup contract. The current preflight is implemented, readiness semantics are correct, tests are hermetic, and the generated preflight result says the environment is not configured: `preflight_not_configured_user_env_needed`.

This round must document and, if appropriate, add a minimal configuration example for the required OllyDbg backend inputs so a future bounded runtime decision can be made only after the user has configured the environment and rerun preflight. This is still a `tool_integration` documentation/config-contract round. It must not launch OllyDbg, x64dbg, IDA/Ghidra, Frida, sidecars, debuggers, runtime probes, or samples.

## 2. Current Evidence

- The previous accepted-with-limitations round is `decision_20260609_fix_ollydbg_preflight_hermetic_tests_v1` / `round_20260609_fix_ollydbg_preflight_hermetic_tests_v1`.
- The accepted implementation has `ready`, `backend_ready`, and `runtime_ready` semantics, where `ready == runtime_ready`.
- The accepted tests are hermetic and no longer depend on local OllyDbg, ollyscript, or sample installation state.
- `project_state/ollydbg_preflight_result.json` reports `ready=false`, `backend_ready=false`, `runtime_ready=false`, and recommendation `preflight_not_configured_user_env_needed`.
- Required environment/configuration inputs include at least:
  - `REVERSE_AGENT_OLLYDBG_PATH`
  - `REVERSE_AGENT_SAMPLE_PATH`
  - availability of the OllyDbg Python scripting bridge/module checked by `ollydbg_preflight.py`
  - existing `reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py`
- The last accepted report had a non-blocking template wording issue: it said source modules were not modified while source changes were listed. This round must avoid that wording; use `no source changes outside allowed scope` if source/report language is needed.
- `negative_results.json` continues to prohibit blind solver/search directions, only increasing beam/budget, `compare_semantics_agree=false` primary frontier, full `solve_reports/` commits, and repeated blocked Base64/RC4/material-hook directions.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.

## 3. Do Not Do

- Do not execute samples.
- Do not launch OllyDbg, x64dbg, IDA, Ghidra, Frida, debugger, emulator, sidecar, hook, or runtime probe.
- Do not attach to any process.
- Do not run script injection.
- Do not run solvers, compare-aware search, brute force, beam expansion, budget expansion, topN expansion, or candidate validation.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify training status, sample metadata, archive directories, artifact freshness, status overlay, or runtime artifacts.
- Do not implement debugger functionality that OllyDbg/x64dbg already provides.
- Do not change readiness semantics unless a small documentation/test assertion requires clarification without behavior change.
- Do not treat `task_packet.task` or `derived_task` as execution authority.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/ollydbg_preflight_result.json`
- `reverse_agent/ollydbg_preflight.py`
- `tests/test_ollydbg_preflight.py`
- `.codex-skills/registry.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

Required repository search / bounded inspection:

- existing README or docs that mention OllyDbg, x64dbg, IDA, Ghidra, debugger, preflight, tool path, sample path, or environment variables
- existing config/example files such as `.env.example`, config templates, CLI docs, or tool setup docs, if present

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
6. Confirm current preflight result is `preflight_not_configured_user_env_needed` and explain why this is an environment/configuration blocker, not a solver or sample-analysis blocker.
7. Inventory the exact user-facing setup inputs required for the OllyDbg preflight to become runtime-ready.
8. Add or update a small, focused setup document or config example that explains:
   - what `REVERSE_AGENT_OLLYDBG_PATH` should point to
   - what `REVERSE_AGENT_SAMPLE_PATH` should point to
   - how to rerun `python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json`
   - how to interpret `backend_ready`, `runtime_ready`, and `ready`
   - that a future bounded runtime probe decision is only allowed after preflight reports runtime readiness or after a manual blocker is explicitly accepted
9. Keep the documentation/tool contract aligned with existing preflight field names and recommendations.
10. Avoid inaccurate report wording such as `source modules were not modified` if any allowed source/doc files are changed; use `no changes outside allowed scope`.
11. Cross-check `negative_results.json`; state explicitly that this setup-contract work does not repeat blocked solver/probe directions.
12. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
13. Confirm no external reverse tool or sample was launched.
14. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.
15. Confirm generated JSON/report/pytest summaries use the same recommendation category.

## 6. Implementation Scope

Allowed changes:

1. A focused documentation file, preferably under an existing docs/tooling location if present, describing OllyDbg backend setup and preflight interpretation.
2. An example config file only if the repository already uses such examples or if adding one is minimal and conventional, for example `.env.example` or `docs/tooling/ollydbg_backend_setup.md`. Do not create a broad new configuration system.
3. Optional minor update to README or existing docs index only if needed to make the setup document discoverable.
4. `project_state/codex_execution_report.md`, updated for this round.
5. `project_state/pytest_result.txt`, updated with real final command outputs for this round.
6. Optional regeneration of `project_state/ollydbg_preflight_result.json` only if the preflight command is rerun as part of tests; do not alter runtime artifacts beyond this compact preflight JSON.

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
- setup documentation/config example exists and is consistent with `ollydbg_preflight.py`
- generated JSON, report summary, and pytest_result summary use the same recommendation
- no external reverse tool/sample execution
- no full `solve_reports/` inspection
- next recommendation is exactly one of:
  - `blocked_waiting_for_user_ollydbg_env_config`
  - `ready_for_bounded_ollydbg_runtime_decision_after_user_preflight`
  - `needs_config_contract_rework`

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- adding setup documentation/config requires broad refactoring or a new configuration system
- deciding readiness requires launching OllyDbg/x64dbg/IDA/Ghidra/Frida, a sidecar, or a sample binary
- final recommendation cannot be reduced to exactly one allowed category
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- JSON validation is not recorded
- report/test IDs mismatch
- any task shifts this round into sample solving, reverse execution, solver work, runtime probing, or training dataset work

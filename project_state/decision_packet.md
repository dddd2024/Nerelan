```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_ollydbg_backend_preflight_config_v1","round_id":"round_20260609_ollydbg_backend_preflight_config_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Advance the accepted single-step interface audit into a minimal OllyDbg backend configuration/preflight step. The previous accepted audit concluded that reverse-agent should reuse the existing debugger step interface, specifically the existing OllyDbg single-step infrastructure, and that the remaining gap is backend/runtime environment configuration rather than missing step logic.

This round must add or verify a non-invasive preflight path that can report whether the OllyDbg backend is configured well enough for a future bounded runtime probe. The preflight must not launch OllyDbg, attach to a process, execute a sample, inject scripts, run a sidecar, or perform runtime probing. It should only inspect repository configuration, environment variables, declared tool paths, and required script/module presence.

## 2. Current Evidence

- The previous accepted repair round is `decision_20260609_fix_single_step_audit_pytest_record_v1` / `round_20260609_fix_single_step_audit_pytest_record_v1`.
- The accepted report category is `reuse_existing_debugger_step_interface`.
- The accepted report states that the existing OllyDbg single-step infrastructure is feature-ready and includes step, register read, exception capture, and max-step limits.
- The accepted report also states that `step_api_unavailable` is caused by `ollydbg_backend_not_configured`, not by missing step logic.
- Current sample state still points at `samplereverse` and `window_lifecycle_no_window_created`, but this round is not a sample-solving round.
- `negative_results.json` continues to prohibit blind solver/search directions, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports/`, and repeating blocked Base64/RC4/material-hook directions.
- Existing mature tools such as OllyDbg/x64dbg/IDA/Ghidra should be reused instead of reimplemented. This round must not implement a debugger; it may only add project-side configuration/preflight structure needed to call an existing backend safely in a future round.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` is advisory only.

## 3. Do Not Do

- Do not execute any sample binary, including `samplereverse`, `Cpp2.exe`, or any local training sample.
- Do not launch OllyDbg, x64dbg, IDA, Ghidra, Frida, debugger, emulator, sidecar, hook, winpty, console validator, or binary instrumentation.
- Do not attach to any process.
- Do not run runtime probes or script injection.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run solvers, compare-aware search, brute force, beam expansion, budget expansion, topN expansion, or Base64/RC4/DES/XOR solver work.
- Do not implement debugger functionality that OllyDbg/x64dbg already provides.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
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

Required repository inspection:

- `reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py`
- `reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py`
- `reverse_agent/strategies/compare_aware_search.py`, only the bounded functions related to post-entry step audit, payload building, OllyDbg/sidecar invocation, and fallback routing
- existing CLI/config modules that might already define tool paths or runtime backend options
- tests mentioning OllyDbg, debugger backend, preflight, tool configuration, project_state lint/report, or compare-aware runtime audit

Optional bounded inspection:

- README or docs that mention OllyDbg/x64dbg/IDA/Ghidra integration
- source modules that already expose StructuredEvidence/tool artifact schemas, only if needed to keep preflight output consistent with existing artifact/report conventions

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == tool_integration`.
4. Confirm both profiles resolve to active registry skills:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm the previous accepted result was `reuse_existing_debugger_step_interface` and that this round is acting on that recommendation.
7. Inventory the exact configuration values the existing OllyDbg step path needs before a future runtime probe, such as tool executable path, script path, Python bridge/module availability, target path declaration, working directory, output path, timeout/step limits, and artifact provenance fields.
8. Check whether the repository already has a config/preflight abstraction for reverse tools; reuse it if present.
9. If no suitable preflight exists, implement the smallest project-side preflight that does not launch any external tool. It should return structured status such as `ready`, `not_configured`, or `missing_dependency`, with actionable missing fields.
10. Ensure the preflight distinguishes mature-tool capability from project-wrapper readiness. For example, OllyDbg may support stepping manually, but reverse-agent must still report whether its wrapper/config is ready.
11. Ensure preflight output is small and suitable for `project_state`/report evidence; do not write bulky runtime artifacts.
12. Cross-check `negative_results.json`; state explicitly that this configuration/preflight work does not repeat blocked solver/probe directions.
13. Confirm no sample execution, debugger/emulator launch, IDA/Ghidra launch, Frida/OllyDbg/x64dbg run, sidecar execution, runtime probing, solver work, or candidate validation occurred.
14. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
15. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.

## 6. Implementation Scope

Allowed changes:

1. A minimal source change for OllyDbg backend configuration/preflight, only if no existing preflight abstraction can be reused. Prefer the smallest cohesive module or function near existing tool/config code.
2. Focused tests for the preflight/config behavior using mocked paths/environment only. Tests must not launch external tools.
3. `project_state/codex_execution_report.md`, updated with the audit result, files changed, preflight behavior summary, and next recommendation.
4. `project_state/pytest_result.txt`, updated with real final command outputs for this round.
5. Optional compact JSON under `project_state/ollydbg_backend_preflight_audit_20260609.json` if useful; if created, list it in `generated_artifacts` and validate it with `python -m json.tool`.

Disallowed changes:

- `.codex-skills/`
- solver code
- sample metadata
- training status
- status overlay
- artifact freshness
- archive directories
- runtime artifacts
- full `solve_reports/`
- any code that directly launches or drives OllyDbg/x64dbg/IDA/Ghidra/Frida in this round

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Also run focused tests for any new or modified preflight logic, for example:

```bash
python -m pytest <focused_preflight_tests>
```

If an optional JSON artifact is created, run and record:

```bash
python -m json.tool project_state/ollydbg_backend_preflight_audit_20260609.json > NUL
```

Use the platform-appropriate null sink if not on Windows, and record the actual command used.

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK`
- `tests/test_project_state.py` passes
- focused preflight tests pass, if source/tests were changed
- optional JSON validates if created
- report/test IDs match this decision and round
- report lists all files changed
- no external reverse tool or sample was launched
- no full `solve_reports/` inspection occurred
- next recommendation is exactly one of:
  - `preflight_ready_for_bounded_ollydbg_runtime_decision`
  - `preflight_not_configured_user_env_needed`
  - `preflight_blocked_missing_existing_wrapper`
  - `preflight_requires_design_rework`

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if any of the following occurs:

- determining readiness requires launching OllyDbg/x64dbg/IDA/Ghidra/Frida, a sidecar, or a sample binary
- a needed config/preflight change would require broad refactoring outside the existing tool/config boundary
- a needed change would duplicate mature debugger functionality instead of wrapping/configuring it
- repository search cannot identify the existing OllyDbg step path or its configuration needs
- final recommendation cannot be reduced to exactly one allowed category
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- `pytest_result.txt` cannot be updated with real outputs from this round
- report/test IDs mismatch
- any task shifts this round into sample solving, reverse execution, solver work, or training dataset work

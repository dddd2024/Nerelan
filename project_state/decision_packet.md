```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_ollydbg_env_contract_recommendation_consistency_v1","round_id":"round_20260609_fix_ollydbg_env_contract_recommendation_consistency_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"tool_integration","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair recommendation-field consistency for the OllyDbg environment setup contract round. The actual `project_state/ollydbg_preflight_result.json` reports `preflight_not_configured_user_env_needed`, but `codex_execution_report.md` and `pytest_result.txt` summaries report `blocked_waiting_for_user_ollydbg_env_config` inside `preflight_result.recommendation`.

This round must separate preflight tool output from next-decision recommendation, or otherwise make the fields consistent. Do not change preflight runtime behavior.

## 2. Current Evidence

- `docs/tooling/ollydbg_backend_setup.md` exists and covers the expected setup contract.
- `.env.example` exists and includes the two required environment variables.
- Actual preflight JSON says `recommendation: preflight_not_configured_user_env_needed`.
- Report and pytest summary currently say `preflight_result.recommendation: blocked_waiting_for_user_ollydbg_env_config`.
- The mismatch violates the previous decision's acceptance requirement that generated JSON, report summary, and pytest_result summary use the same recommendation.
- `blocked_waiting_for_user_ollydbg_env_config` is a valid next-decision recommendation, but it must not be stored as the actual preflight tool recommendation.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits; this repair round must not execute any of those directions.

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
- Do not change preflight readiness semantics or preflight behavior.
- Do not treat `task_packet.task` or `derived_task` as execution authority.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/ollydbg_preflight_result.json`
- `docs/tooling/ollydbg_backend_setup.md`
- `.env.example`
- `reverse_agent/ollydbg_preflight.py`
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
6. Preserve the actual preflight JSON recommendation: `preflight_not_configured_user_env_needed`.
7. Make `codex_execution_report.md` and `pytest_result.txt` summaries match the actual preflight JSON recommendation.
8. If expressing the next step, use a separate field such as `next_decision_recommendation: blocked_waiting_for_user_ollydbg_env_config`.
9. Confirm generated JSON, report summary, and pytest_result summary no longer conflict.
10. Confirm docs and `.env.example` remain consistent with `ollydbg_preflight.py`.
11. Cross-check `negative_results.json`; state explicitly that this recommendation-field repair does not repeat blocked solver/probe directions.
12. Confirm no full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` read occurred.
13. Confirm no external reverse tool or sample was launched.
14. Confirm no preflight behavior/readiness semantic changes occurred.
15. Confirm `codex_execution_report.md` and `pytest_result.txt` match this decision id and round id.

## 6. Implementation Scope

Allowed changes only:

1. `project_state/codex_execution_report.md`, to correct summary fields and explain the preflight-vs-next-decision distinction.
2. `project_state/pytest_result.txt`, to record this round's real outputs and corrected summary fields.
3. Optional minor wording correction in `docs/tooling/ollydbg_backend_setup.md` only if needed to clarify `preflight_recommendation` versus `next_decision_recommendation`.
4. Optional regeneration of `project_state/ollydbg_preflight_result.json` only by rerunning the existing preflight command; do not edit the recommendation manually.

No source changes unless strictly necessary, and do not change preflight behavior.

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
- actual preflight JSON, report summary, and pytest_result summary agree on `preflight_not_configured_user_env_needed`
- any next-step recommendation is in a separate field and equals one of:
  - `blocked_waiting_for_user_ollydbg_env_config`
  - `ready_for_bounded_ollydbg_runtime_decision_after_user_preflight`
  - `needs_config_contract_rework`
- no stale old IDs in `pytest_result.txt`
- no external reverse tool/sample execution occurred
- no preflight behavior/readiness semantic changes occurred

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- recommendation fields remain inconsistent
- preflight behavior changes unexpectedly
- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- JSON validation is not recorded
- report/test IDs mismatch
- any task shifts into sample solving, runtime probing, solver work, or external debugger/tool execution

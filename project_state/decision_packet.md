```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_samplereverse_diagnostic_review_schema_v1","round_id":"round_20260609_fix_samplereverse_diagnostic_review_schema_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"reverse_solving","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the diagnostic review report schema and audit evidence without running any new reverse-solving action. The current report uses the invalid recommendation category `evidence_production`; it must be changed to one of the categories explicitly allowed by the active decision. The report must also explicitly verify both active skill profiles: `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.

This is a `reverse_solving` report-schema repair round only. It must not execute the sample, run IDA/Ghidra/debuggers, run sidecars, run solvers, generate candidates, or inspect full `solve_reports/`.

## 2. Current Evidence

- The active previous diagnostic review report is `report_20260609_samplereverse_current_window_diagnostic_review_v1` for `decision_20260609_samplereverse_current_window_diagnostic_review_v1`.
- Its report/test IDs match and `lint-decision`, `lint-report`, and `pytest tests/test_project_state.py` passed.
- The report and `pytest_result.txt` use `next_round_recommendation_category: evidence_production`, but the governing decision required one of five exact categories:
  - `bounded_static_artifact_review_complete_next_decision_needed`
  - `needs_manual_ida_or_x64dbg_tool_integration_decision`
  - `needs_new_bounded_runtime_probe_decision`
  - `needs_project_state_or_artifact_index_repair_decision`
  - `blocked_insufficient_current_artifacts`
- The previous diagnostic review recommends fixing single-step capability, possibly via Frida/x64dbg/OllyDbg backend support, and separately mentions manual IDA/x64dbg handoff-helper inspection. Because the highest-priority proposed action is to obtain new bounded runtime observation, the likely corrected category is `needs_new_bounded_runtime_probe_decision`. If Codex chooses a different allowed category, it must justify the choice from the already recorded report facts.
- Active decision metadata declares both `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
- `.codex-skills/registry.json` records `reverse-agent-iteration` as active version 2 and `samplereverse-frontier` as active version 2.
- The previous report checklist incorrectly mentioned only `reverse-agent-iteration@v2`; it must explicitly verify both profiles.
- `artifact_index.json` already confirms the diagnostic review used current artifact families from `sr_arg0_hook_readiness_ordering_20260526_r1`. This repair round should not add new artifact conclusions unless needed to correct the schema/report wording.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions, full `solve_reports` commits, and several blocked Base64/RC4/material-hook directions. This repair round must not execute any of those directions.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` remains advisory only.

## 3. Do Not Do

- Do not execute any sample binary, including `samplereverse` or `Cpp2.exe`.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, runtime probe, hook, sidecar, winpty, console validator, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run compare-aware search, old `sample_solver` blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any solver action.
- Do not rerun previous failed directions from `negative_results.json`.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify source modules.
- Do not modify training status, sample metadata, status overlay, archive directories, runtime artifacts, artifact freshness, or solver code.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not promote stale or unknown-freshness artifacts to current evidence.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/task_packet.json`

Optional bounded files, only if needed to preserve wording from the existing diagnostic review:

- `project_state/current_state.json`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == reverse_solving`.
4. Confirm both skill profiles resolve to active registry skills:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Replace the invalid `evidence_production` recommendation category with exactly one of the five allowed values:
   - `bounded_static_artifact_review_complete_next_decision_needed`
   - `needs_manual_ida_or_x64dbg_tool_integration_decision`
   - `needs_new_bounded_runtime_probe_decision`
   - `needs_project_state_or_artifact_index_repair_decision`
   - `blocked_insufficient_current_artifacts`
7. If selecting `needs_new_bounded_runtime_probe_decision`, state that this means a future decision must define the bounded runtime/single-step work; do not run it here.
8. If selecting `needs_manual_ida_or_x64dbg_tool_integration_decision`, state that this means a future tool-integration/manual-inspection decision is needed; do not run it here.
9. Update both `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` so their `next_round_recommendation_category` values match.
10. Confirm no new reverse execution, runtime probing, debugger, emulator, sidecar, solver, candidate validation, IDA/Ghidra run, or source-code change occurred.
11. Confirm stale artifacts remain stale and are not promoted as current evidence.
12. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
13. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes only:

1. `project_state/codex_execution_report.md`, updated to correct the recommendation category and explicitly audit both skill profiles.
2. `project_state/pytest_result.txt`, updated with this round's command outputs and the corrected matching recommendation category.

Do not modify source modules, `.codex-skills/`, training status, sample metadata, status overlay, archive files, runtime artifacts, solver code, artifact freshness, or full `solve_reports/`.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK`
- `pytest tests/test_project_state.py` passes
- report/test IDs match this decision and round
- `next_round_recommendation_category` is one of the five allowed values
- report and `pytest_result.txt` use the same recommendation category
- both `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are explicitly audited as active
- no runtime/reverse execution occurred

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- final `lint-decision` fails
- final `lint-report` fails
- pytest fails
- report still uses an invalid recommendation category
- report and `pytest_result.txt` disagree on recommendation category
- either skill profile cannot be resolved as active
- any task requires new runtime/debugger/IDA/Ghidra/solver execution
- any source, skill, artifact, archive, training status, or full `solve_reports/` modification becomes necessary

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_resolve_harness_repair_action_live_state_rework_v1","round_id":"round_20260610_resolve_harness_repair_action_live_state_rework_v1","based_on_state_build_id":"state_20260610_081228_6c1551059244","based_on_state_digest":"6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Fix the live-state mismatch from `decision_20260610_resolve_harness_artifact_repair_action_v1`.

The prior report claims that `repair_harness_artifact` was resolved into precise actions (`select_fallback_harness_run` when a complete fallback exists, or `rebuild_harness_artifact` when none exists). However, live `model_gate.json`, live `task_packet.json`, and post-archive status still show the generic `repair_harness_artifact` action. This round must connect the implemented logic to `python -m reverse_agent.project_state build` and regenerate live state so the precise action is visible in `model_gate.json`, `task_packet.json`, and final status.

This is an `engineering_branch` live-state rework round. It must not enter reverse solving or execute samples/tools.

## 2. Current Evidence

- Current decision before this packet was `decision_20260610_resolve_harness_artifact_repair_action_v1`.
- Its report is bound to that decision and says `status: SUCCESS`.
- The report claims `build_model_gate()` now sets `next_local_action` to `select_fallback_harness_run` when fallback exists, or `rebuild_harness_artifact` when no complete fallback exists.
- The report claims `build_task_packet()` propagates `select_fallback_harness_run` and `rebuild_harness_artifact` as precise task names.
- Live `model_gate.json` still reports `next_local_action: repair_harness_artifact`.
- Live `task_packet.json` still reports `task: repair_harness_artifact` and `next_local_action: repair_harness_artifact`.
- Post-archive status for the prior round still reports `task: repair_harness_artifact` and `derived_task: repair_harness_artifact`.
- The prior round did not record `python -m reverse_agent.project_state build` or `python -m reverse_agent.project_state lint-decision --state-dir project_state` in `pytest_result.txt`.
- The prior round ran `python -m pytest tests/test_project_state.py -q` only, not the required combined `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q`.
- Latest harness run remains `solve_reports\harness_runs\samplereverse_exact1_projected_vs_neighbor_20260424`, with `summary.json` present but `case_results/` missing.
- Current state anchor remains `state_20260610_081228_6c1551059244` with digest `6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936`.
- Stale/missing artifacts must not be promoted to current.
- `.codex-skills/registry.json` has active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.

## 3. Do Not Do

- Do not run any sample binary.
- Do not run the harness on a sample.
- Do not generate, mutate, rank, or validate candidates.
- Do not run solver/search expansion.
- Do not run runtime probe, debugger, emulator, hook, sidecar, IDA, Ghidra, OllyDbg, or x64dbg.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not change sample binaries, candidate files, training data, or status overlays.
- Do not promote stale/missing artifacts to current.
- Do not treat a run without `case_results/` as inspectable failed-case evidence.
- Do not create synthetic `case_results/` that pretend a sample was executed.
- Do not silently promote a fallback harness run to current/latest.

## 4. Files To Inspect

Required project-state files:

- `project_state/decision_packet.md`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`

Required source/test files:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Allowed bounded harness metadata inspection:

- Directory existence/listing for `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/`
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- Bounded metadata-only listing of sibling `solve_reports/harness_runs/*` directory names and their `summary.json` / `run_manifest.json` / `case_results/` presence only when needed to test fallback detection.

Do not open full case result payloads except existence/count metadata. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Inspect the previous changes in `reverse_agent/project_state.py` and identify why the precise action logic is not reflected in live `model_gate.json` / `task_packet.json` after status/archive.
4. Run `python -m reverse_agent.project_state build` and inspect the regenerated live `model_gate.json` and `task_packet.json`.
5. If build still leaves `next_local_action` / `task` as generic `repair_harness_artifact`, fix the disconnected code path in `reverse_agent/project_state.py`.
6. Ensure live `model_gate.json` resolves the current condition to one of:
   - `next_local_action: select_fallback_harness_run` with explicit fallback provenance; or
   - `next_local_action: rebuild_harness_artifact` when no complete compatible fallback exists.
7. Ensure live `task_packet.json` resolves the current condition to one of:
   - `task: select_fallback_harness_run` with explicit fallback provenance; or
   - `task: rebuild_harness_artifact` when no complete compatible fallback exists.
8. Ensure `task_packet.json` does not revert to generic reverse-solving `collect_missing_evidence`.
9. Ensure `task_packet.json` does not remain at generic `repair_harness_artifact` unless the report proves that `repair_harness_artifact` is intentionally now the exact terminal action. Prefer `rebuild_harness_artifact` / `select_fallback_harness_run` because that was the prior decision requirement.
10. Preserve backward compatibility for existing fields consumed by tests or UI.
11. Ensure stale/missing artifacts remain stale/missing unless current provenance is created by existing build tooling.
12. Update focused regression tests so the build path, not just helper functions, produces the precise live action.
13. Run the required tests and record exact command outputs in live `project_state/pytest_result.txt`.
14. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
15. Archive this round after live report/test/state files are updated.
16. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.
17. Ensure no sample/tool/debugger/solver/probe execution occurred.
18. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to connecting fallback/rebuild action resolution to the actual project-state build path and status output.
- `tests/test_project_state.py`, limited to focused regression tests for build-path live action resolution.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by harness artifact metadata compatibility.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_resolve_harness_repair_action_live_state_rework_v1/*`, minimal archive only

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`

## 7. Tests

Run and record exact outputs:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_resolve_harness_repair_action_live_state_rework_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Live `model_gate.json` must no longer remain at generic `next_local_action: repair_harness_artifact`, unless the report proves that this exact value is intentionally now the terminal precise action.
- Preferred accepted outputs are `next_local_action: rebuild_harness_artifact` when no complete compatible fallback exists, or `next_local_action: select_fallback_harness_run` with explicit fallback provenance when one exists.
- Live `task_packet.json` must no longer remain at generic `task: repair_harness_artifact`, unless the report proves that this exact value is intentionally now the terminal precise action.
- Preferred accepted outputs are `task: rebuild_harness_artifact` or `task: select_fallback_harness_run`.
- Latest incomplete harness run remains explicitly classified as `invalid_or_incomplete`.
- If fallback is selected, fallback provenance is explicit and the fallback run is not silently promoted as latest/current.
- If no fallback is selected, rebuild action is explicit.
- `task_packet.json` must not revert to `collect_missing_evidence` for this condition.
- Focused regression tests cover the actual build path.
- `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q` passes.
- `lint-report: OK` after live report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Resolving the live action requires running a sample binary.
- Resolving the live action requires running the harness on a sample.
- Resolving the live action requires solver/search/candidate generation/candidate validation.
- Resolving the live action requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Resolving the live action requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent fallback or rebuild action without breaking existing state consumers.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```
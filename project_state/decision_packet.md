```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_samplereverse_current_window_diagnostic_review_v1","round_id":"round_20260609_samplereverse_current_window_diagnostic_review_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"reverse_solving","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Resume the `samplereverse` reverse-solving mainline with a bounded diagnostic review of the current window-lifecycle stall evidence. The goal is to determine, from already indexed current artifacts only, what the next evidence-producing action should be for the `window_lifecycle_no_window_created` bottleneck.

This round is evidence review and planning, not execution of a new probe. It must not run the sample, debugger, emulator, IDA/Ghidra, sidecars, solvers, or candidate search. It must produce a clear, auditable recommendation for the next round, grounded in current artifact freshness and negative-results constraints.

## 2. Current Evidence

- The immediately preceding engineering repair round was accepted: `decision_20260609_fix_archive_evidence_lint_report_record_v1` / `report_20260609_fix_archive_evidence_lint_report_record_v1` / `round_20260609_fix_archive_evidence_lint_report_record_v1` now have matching IDs and recorded `lint-report: OK` plus `pytest tests/test_project_state.py` passing with 158 tests.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json` is advisory only and still carries the sample-derived task `Review bounded window discovery diagnostics`.
- `current_state.json` is still a `sample_state` for `samplereverse`, with `current_bottleneck.reason = window_lifecycle_no_window_created` and `current_bottleneck.stage = compare_handoff_narrower_post_entry_breakpoint_audit`.
- Current best candidates remain partial and are not solution evidence: exact2 has prefix `78d540b49c590770`, exact1/frontier has prefix `5a3e7f46ddd474d0`, and both are only search-frontier context. Do not generate or validate new candidates in this round.
- `artifact_index.json` contains many stale reverse-solving artifacts and a smaller set of current artifacts from `sr_arg0_hook_readiness_ordering_20260526_r1`. Only artifacts marked `freshness: current` in `latest_artifacts_v2` may be used as current evidence.
- Relevant current artifact families to verify in `artifact_index.json` before reading include, if marked current: `compare_handoff_narrower_post_entry_breakpoint_audit`, `compare_handoff_post_entry_step_runtime_audit`, `compare_handoff_path_divergence_audit`, `compare_handoff_branch_operand_runtime_audit`, `compare_handoff_edge_operand_provenance_audit`, `compare_handoff_exit_classifier_audit`, `compare_hook_path_reachability_audit`, `compare_real_lhs_provenance_audit`, `run_manifest`, and `summary`.
- Stale artifacts such as old Base64/RC4 probes, old compare probes, old pairscan/guided results, and legacy tool artifacts may be used only as historical context if explicitly labeled stale; they must not drive a new claim.
- `negative_results.json` prohibits returning to old `sample_solver` blind search, only increasing beam/budget, using `compare_semantics_agree=false` candidates as primary frontier, committing full `solve_reports/`, repeating prior fixed candidate sets, repeating current transform trace consistency without new runtime evidence, and several blocked Base64/RC4/material-hook directions.
- Existing relevant capabilities include project-state status/lint/report tooling, artifact indexing, compare-aware strategy code, harness-generated runtime artifacts, solver templates, and mature reverse tools such as IDA/Ghidra/debuggers. Mature reverse tools are not to be run in this review round; if the evidence points to manual IDA/x64dbg work, that must be proposed as a separate future decision.
- No current IDA/Ghidra artifact is available for this round unless `artifact_index.json` explicitly marks one current; do not claim IDA/Ghidra has proven anything without current provenance.

## 3. Do Not Do

- Do not execute any sample binary, including `samplereverse` or `Cpp2.exe`.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, runtime probe, hook, sidecar, winpty, console validator, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run compare-aware search, old `sample_solver` blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any solver action.
- Do not rerun previous failed directions from `negative_results.json` unless this report documents a specific new current artifact that justifies a future override; even then, do not execute the override in this round.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify source modules.
- Do not modify training status, sample metadata, status overlay, archive directories, or runtime artifacts.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not promote stale or unknown-freshness artifacts to current evidence.

## 4. Files To Inspect

Required project-state files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`

Required bounded artifact inspection, only after confirming `freshness: current` in `artifact_index.json`:

- current `compare_handoff_narrower_post_entry_breakpoint_audit` artifact
- current `compare_handoff_post_entry_step_runtime_audit` artifact, if present
- current `compare_handoff_path_divergence_audit` artifact, if present
- current `compare_handoff_branch_operand_runtime_audit` artifact, if present
- current `compare_handoff_edge_operand_provenance_audit` artifact, if present
- current `compare_handoff_exit_classifier_audit` artifact, if present
- current `compare_hook_path_reachability_audit` artifact, if present
- current `compare_real_lhs_provenance_audit` artifact, if present
- current `run_manifest` and `summary`, if present

Optional bounded source/test inspection, only to understand artifact schema or report existing fields:

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/function_semantics.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == reverse_solving`.
4. Confirm `decision_meta.skill_profiles == ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]` and both profiles resolve to active registry skills.
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm the prior engineering repair state is clean before this reverse-solving review begins: report/test IDs match and `lint-report` is OK.
7. Confirm each artifact inspected for diagnostic conclusions is marked `freshness: current` in `latest_artifacts_v2`; list any relevant stale artifacts separately as stale-only context.
8. Extract from current artifacts the precise reason the narrower post-entry breakpoint/window lifecycle did not create a window, including any hook miss, reachability, branch outcome, operand provenance, edge classification, or path divergence facts present in the artifacts.
9. Cross-check the extracted facts against `negative_results.json`; explicitly state which blocked directions must remain blocked.
10. Identify the next evidence-producing action as one of these categories, with a justification:
    - `bounded_static_artifact_review_complete_next_decision_needed`
    - `needs_manual_ida_or_x64dbg_tool_integration_decision`
    - `needs_new_bounded_runtime_probe_decision`
    - `needs_project_state_or_artifact_index_repair_decision`
    - `blocked_insufficient_current_artifacts`
11. If proposing a future runtime/debugger/IDA/Ghidra/tool action, define only the future decision's minimal goal, required current evidence, and stop conditions. Do not run it here.
12. Confirm no reverse execution, runtime probing, debugger, emulator, sidecar, solver, candidate validation, or source-code change occurred.
13. Confirm stale artifacts remain stale and are not promoted as current evidence.
14. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
15. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes are limited to current state/report bookkeeping:

1. `project_state/codex_execution_report.md`, updated with the diagnostic review outcome, artifact freshness table, negative-results cross-check, and recommended next decision category.
2. `project_state/pytest_result.txt`, updated with this round's command outputs.
3. Optionally, one compact JSON diagnostic artifact under `project_state/`, named `samplereverse_current_window_diagnostic_review_20260609.json`, if Codex needs a machine-readable summary. If created, list it in `generated_artifacts` and keep it small; do not place it under `solve_reports/`.

Do not modify source modules, `.codex-skills/`, training status, sample metadata, status overlay, archive files, runtime artifacts, solver code, or full `solve_reports/`.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

If an optional JSON diagnostic artifact is created, also run and record:

```bash
python -m json.tool project_state/samplereverse_current_window_diagnostic_review_20260609.json > NUL
```

Use the platform-appropriate null sink if not on Windows, and record the actual command used.

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK`
- `pytest tests/test_project_state.py` passes
- optional diagnostic JSON validates if created
- report/test IDs match this decision and round
- every diagnostic conclusion cites a current artifact or is explicitly labeled stale/unknown
- no sample execution, debugger, emulator, solver, sidecar, candidate validation, IDA/Ghidra run, or source modification occurred

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if any of the following occurs:

- relevant current artifacts are missing or only stale artifacts are available for the diagnostic question
- `artifact_index.json` cannot distinguish current from stale for the artifacts needed
- any required conclusion would depend on full `solve_reports/` scanning
- any required conclusion would require executing samples, running a debugger/emulator/IDA/Ghidra, probing runtime, or validating candidates in this round
- `lint-decision` fails
- final `lint-report` fails
- pytest fails
- `pytest_result.txt` cannot be updated with real outputs from this round
- report/test IDs mismatch
- any task shifts this round into `engineering_branch`, `tool_integration`, or `training_dataset` implementation rather than bounded reverse-solving evidence review

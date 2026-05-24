```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_samplereverse_hook_observation_reliability",
  "round_id": "round_20260523_samplereverse_lhs_last_writer_instrumentation",
  "based_on_decision_id": "decision_20260523_samplereverse_lhs_last_writer_instrumentation",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py",
    "reverse_agent/sidecar_health.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_compare_aware_search_strategy.py",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/strategies/compare_aware_search.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"last_writer or real_lhs or hook_observation or provenance\"",
    "python -m pytest -q tests/test_project_state.py -k \"last_writer or provenance or artifact\"",
    "python -m reverse_agent.harness --dataset solve_reports\\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_hook_observation_reliability_20260524_r1 --reports-dir solve_reports --analysis-mode Auto --model-type \"Copilot CLI\" --runtime-validation-enabled --tool-enabled --case-id samplereverse-compare-producer-backtrace --no-resume",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r1",
    "python -m reverse_agent.harness --dataset solve_reports\\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_hook_observation_reliability_20260524_r2 --reports-dir solve_reports --analysis-mode Auto --model-type \"Copilot CLI\" --runtime-validation-enabled --tool-enabled --case-id samplereverse-compare-producer-backtrace --no-resume",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r2",
    "python -m reverse_agent.harness --dataset solve_reports\\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_hook_observation_reliability_20260524_r3 --reports-dir solve_reports --analysis-mode Auto --model-type \"Copilot CLI\" --runtime-validation-enabled --tool-enabled --case-id samplereverse-compare-producer-backtrace --no-resume",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r3",
    "python -m reverse_agent.harness --dataset solve_reports\\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_hook_observation_reliability_20260524_r4 --reports-dir solve_reports --analysis-mode Auto --model-type \"Copilot CLI\" --runtime-validation-enabled --tool-enabled --case-id samplereverse-compare-producer-backtrace --no-resume",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state"
  ],
  "generated_artifacts": [
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r1/summary.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r1/reports/tool_artifacts/samplereverse_patched/post_handoff_exception_unwind_audit/post_handoff_exception_unwind_audit.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r2/summary.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r2/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r3/summary.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r3/reports/tool_artifacts/samplereverse_patched/post_handoff_exception_unwind_audit/post_handoff_exception_unwind_audit.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/summary.json",
    "solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json",
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/model_gate.json",
    "project_state/negative_results.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "next_suggested_task": [
    "Use the r4 raw write samples to trace why followed current-thread writes remain before/outside the actual compare arg0 window.",
    "Keep Base64/RC4 breakpoint probing blocked until an arg0-intersecting runtime-backed writer is identified."
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-24 samplereverse hook observation reliability

Result: `SUCCESS` / `ACCEPTED`. The same-process sidecar no longer collapses the current failure into a generic no-observation timeout. It now records per-hook observation liveness, post-UI observation counts, hook-hit counts, and write-monitor health on every same-process hook observation, not only on the static compare hook.

## Changes

- `compare_pre_compare_handoff_target_probe.py`
  - Added observation timestamps, `observation_count`, `post_ui_observation_count`, `hook_hit_counts_by_name`, first/last observation timing fields, and `last_observation_hook_name`.
  - Added `hook_installed_but_not_hit_after_ui_trigger` for the precise case where hooks are installed, the UI button is triggered, and no same-process hook observation is captured.
  - Flushes `write_monitor_health` with every hook observation so current-thread Stalker activation is visible as soon as an upstream hook fires.
- `compare_aware_search.py` and `sidecar_health.py`
  - Preserve the new lifecycle/observation fields through candidate rows, sidecar health, aggregate payloads, and candidate execution health.
  - Normalize old `hook_not_hit` rows with `button_triggered + observation_count=0` into `hook_installed_but_not_hit_after_ui_trigger`.
  - Keep `compare_probe_fallback_is_provenance=false`; fallback compare args remain diagnostic-only.
- Tests
  - Updated last-writer hook-observation regression coverage for the new precise classification and observation fields.

## Runtime Evidence

Final accepted run:

`solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json`

Key fields:

| field | value |
|---|---|
| classification | `compare_lhs_runtime_backed_writer_missing` |
| runtime_backed_count | `3` |
| write_monitor_health.observed_candidate_count | `3` |
| write_monitor_health.followed_thread_count | `6` |
| write_monitor_health.raw_write_count | `27` |
| write_monitor_health.filtered_intersecting_write_count | `0` |
| write_monitor_health.selected_thread_ids | `10576`, `11928`, `32264` |
| write_monitor_health.follow_attempt_stages | `upstream_candidate_context` |
| last_writer_summary.raw_write_event_count | `27` |
| last_writer_summary.retained_write_count | `0` |
| last_writer_summary.connects_to_actual_arg0 | `false` |
| breakpoint_probe_allowed | `false` |

This moves the bottleneck back out of `instrumentation_incomplete`: same-process hooks now fire, Stalker follows the current runtime threads, and raw writes are captured. The remaining problem is that none of those raw writes intersect the actual compare arg0 buffer before `0x258c`.

## Verification

| command | result |
|---|---|
| `python -m py_compile reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/strategies/compare_aware_search.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py -k "last_writer or real_lhs or hook_observation or provenance"` | passed, `40 passed, 154 deselected` |
| `python -m pytest -q tests/test_project_state.py -k "last_writer or provenance or artifact"` | passed, `10 passed, 116 deselected` |
| `python -m reverse_agent.harness ... --run-name sr_lhs_hook_observation_reliability_20260524_r1 ...` | completed, generated `post_handoff_exception_unwind_audit`, classification `seh_unwind_to_compare_path` |
| `python -m reverse_agent.harness ... --run-name sr_lhs_hook_observation_reliability_20260524_r2 ...` | completed, generated pre-flush `compare_real_lhs_provenance_audit`, classification `instrumentation_incomplete`; exposed upstream observations without aggregate thread-follow health |
| `python -m reverse_agent.harness ... --run-name sr_lhs_hook_observation_reliability_20260524_r3 ...` | completed, refreshed precursor `post_handoff_exception_unwind_audit`, classification `seh_unwind_to_compare_path` |
| `python -m reverse_agent.harness ... --run-name sr_lhs_hook_observation_reliability_20260524_r4 ...` | completed, generated accepted `compare_real_lhs_provenance_audit`, classification `compare_lhs_runtime_backed_writer_missing` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4` | passed |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed; latest run is `sr_lhs_hook_observation_reliability_20260524_r4`, `missing=[]`, reason `compare_lhs_runtime_backed_writer_missing` |

## Guardrails

- No Base64/RC4 breakpoint probe was run.
- No old `sample_solver` path was used.
- No search, beam, budget, topN, timeout, frontier, ranking, or candidate-generation expansion was made.
- `PROJECT_PROGRESS_LOG.txt` was not modified.

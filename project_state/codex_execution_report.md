```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260526_reverse_arg0_ui_trigger_timing_validation",
  "round_id": "round_20260526_reverse_arg0_ui_trigger_timing_validation",
  "based_on_decision_id": "decision_20260526_reverse_arg0_ui_trigger_timing_validation",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/decision_packet.md",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py",
    "reverse_agent/sidecar_health.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "reverse_agent/project_state.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_project_state.py"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py reverse_agent/sidecar_health.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"arg0 or hook or timeout or observation or ui or trigger or timing or classification\"",
    "python -m pytest -q tests/test_project_state.py -k \"sidecar or ui or trigger or timing or observation or blocker or report or runtime\"",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check"
  ],
  "generated_artifacts": [
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "next_suggested_task": [
    "Run one bounded UI timing validation with sr_arg0_ui_trigger_timing_20260526_r1 if runtime confirmation is required."
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-26 UI Trigger Timing Validation

Result: `PARTIAL` / `NEEDS_REVIEW`.

This round executed `decision_20260526_reverse_arg0_ui_trigger_timing_validation` on the reverse-solving mainline with `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`. The execution authority was `project_state/decision_packet.md`; `task_packet.task` and `derived_task` were treated as derived guidance only.

## Required Audit

| item | result |
|---|---|
| decision_id | `decision_20260526_reverse_arg0_ui_trigger_timing_validation` |
| mainline | `reverse_solving` |
| skill_profiles | `reverse-agent-iteration@v2`, `samplereverse-frontier@v2` |
| selected run | `sr_arg0_bounded_writer_trace_20260525_r1` |
| compare_real_lhs_provenance_audit freshness | `current` |
| compare_probe freshness | `stale`; not used as current provenance |
| previous blocker | `arg0_ui_trigger_or_timeout_blocked` |
| this round goal | validate/fix UI trigger timing path, not final writer |
| forbidden work | no Base64/RC4 probe, old solver, candidate search, beam/budget/timeout/frontier expansion |

## UI Timing Diagnosis

Existing selected-run per-candidate artifacts were sufficient to prove the old telemetry was incomplete, but not sufficient to prove the runtime order. Each row had script load, callback-before-load, hook install, and button trigger evidence, but lacked hook/UI timestamps and root-cause classification. Therefore this round did not claim final-writer provenance or post-ui observations from stale/partial evidence.

| candidate_hex | process_spawned | frida_attached | script_loaded | callback_before_load | hooks_installed | hook_count | install_errors | hooks_installed_timestamp_ms | ui_trigger_start_timestamp_ms | ui_trigger_end_timestamp_ms | ui_trigger_status | ui_after_hooks | python_messages | observation_count | post_ui_observation_count | hook_hits | timeout_or_wait_reason | root_cause_classification |
|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---|---|---|
| `78d540b49c59077041414141414141` | unknown | unknown | loaded | true | installed | 4 | 0 | missing | missing | missing | button_triggered | false | 116 | 0 | 0 | none | missing | telemetry/barrier contract missing in old artifact |
| `5a3e7f46ddd474d041414141414141` | unknown | unknown | loaded | true | installed | 4 | 0 | missing | missing | missing | button_triggered | false | 22 | 0 | 0 | none | missing | telemetry/barrier contract missing in old artifact |
| `78d540b49c59076f41414141414141` | unknown | unknown | loaded | true | installed | 4 | 0 | missing | missing | missing | button_triggered | false | 23 | 0 | 0 | none | missing | telemetry/barrier contract missing in old artifact |

Conclusion:

```text
actual_ordering_bug = not proven by old artifact
telemetry_ordering_bug = possible; old artifact has false ordering with missing timing fields
hooks_ready_barrier_missing = fixed in code by waiting within the existing 1s window before UI trigger
ui_trigger_timeout_or_window_too_early = still possible until bounded rerun
target_path_or_process_mismatch = not indicated by selected run
still_runtime_blocked = yes, until a bounded runtime rerun proves post-ui observations or hook-ready/no-hit
```

Current selected runtime artifact remains:

```text
solve_reports/harness_runs/sr_arg0_bounded_writer_trace_20260525_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

No new runtime artifact was generated. The planned run name `sr_arg0_ui_trigger_timing_20260526_r1` remains unused because the code-level telemetry contract and projection behavior were validated by focused tests first, and the selected run cannot retroactively supply the missing timestamp fields.

## Implementation

Updated `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py` to emit additive lifecycle fields:

```text
process_spawned_at_ms
frida_attached_at_ms
script_load_start_at_ms
script_loaded_at_ms
message_callback_registered_at_ms
hooks_install_begin_at_ms
hooks_installed_at_ms
ui_trigger_start_at_ms
ui_trigger_end_at_ms
hooks_ready_barrier_seen
hooks_ready_barrier_wait_ms
hooks_ready_before_ui_trigger
ui_trigger_timing_status
timeout_or_wait_reason
```

The Python message callback remains registered before `script.load()`. The UI trigger now waits for the hooks-installed message inside the existing 1-second pre-window instead of expanding the bounded runtime timeout or search budget.

Updated `reverse_agent/strategies/compare_aware_search.py` and `reverse_agent/sidecar_health.py` so the new timing fields survive per-candidate payloads, aggregate `candidate_execution_health`, `candidate_results`, and normalized sidecar health.

Updated `reverse_agent/project_state.py` to project UI timing blockers into the approved classification set:

```text
arg0_ui_trigger_timing_fixed_observations_available
arg0_hooks_ready_but_not_hit
arg0_hooks_ready_message_delivery_failed
arg0_ui_trigger_barrier_missing_fixed
arg0_ui_trigger_timing_telemetry_bug_fixed
arg0_ui_trigger_or_timeout_blocked
arg0_target_path_or_process_mismatch
arg0_writer_trace_runtime_blocked
```

The rebuilt active state still reports:

```text
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = inconclusive
current_bottleneck.blocker = arg0_ui_trigger_or_timeout_blocked
```

This is expected because the selected runtime artifact predates the new timing fields.

## Evidence Rules Preserved

```text
compare_probe_fallback_is_provenance = false
stale compare_probe was not used as current evidence
fallback-only 0x258c did not become runtime-backed actual_arg0
hook installed was not treated as hook hit
slot pointer/write evidence was not treated as final data writer evidence
UI timing blocker was not collapsed back to arg0_final_writer_trace_schema_gap
```

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py reverse_agent/sidecar_health.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or hook or timeout or observation or ui or trigger or timing or classification"` | passed, `49 passed, 147 deselected` |
| `python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime"` | passed, `59 passed, 85 deselected` |
| `python -m pytest -q tests/test_project_state.py` | passed, `144 passed` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1` | passed; rebuilt active project_state from selected run |
| `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed after refreshing decision metadata to state `state_20260526_080937_c7583ea6dc32` |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed; report matches decision, status is `PARTIAL`, archive status is `not_archived` |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed with warnings: `report_status is PARTIAL`, `report round not archived yet` |
| `git diff --check` | passed; Git reported line-ending normalization warnings only |

## Git Diff Summary

Diff scope is limited to active `project_state` records, sidecar timing telemetry, sidecar health normalization, compare-aware aggregation, project-state blocker projection, and focused tests. No full `solve_reports` directory was added, no runtime rerun was performed, no archive-round was executed, and no Base64/RC4 probe or candidate search was run.

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260525_reverse_arg0_final_data_writer_trace",
  "round_id": "round_20260525_reverse_arg0_final_data_writer_trace",
  "based_on_decision_id": "decision_20260525_reverse_arg0_final_data_writer_trace",
  "status": "SUCCESS",
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
    "reverse_agent/project_state.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_project_state.py"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"arg0 or pointer or writer or raw_write or provenance or classification\"",
    "python -m pytest -q tests/test_project_state.py -k \"artifact or provenance or bottleneck or decision or report or pointer or writer\"",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260525_reverse_arg0_final_data_writer_trace"
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
    "Run one bounded sidecar rerun with the new arg0_final_data_writer_trace fields to capture module+0x253a, module+0x2559, module+0x258b, and module+0x258c rows for the fixed current candidates."
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-25 Arg0 Final Data Writer Trace

Result: `SUCCESS` / `NEEDS_REVIEW`.

This round executed `decision_20260525_reverse_arg0_final_data_writer_trace` against the selected run `sr_lhs_hook_observation_reliability_20260524_r4`. No harness was run, no new runtime artifact was produced, and no Base64/RC4 probe, old solver, candidate search, beam, frontier, timeout, or budget expansion was used.

## Scope Audit

| item | result |
|---|---|
| decision id | `decision_20260525_reverse_arg0_final_data_writer_trace` |
| decision status | `APPROVED` |
| mainline | `reverse_solving` |
| skill profiles | `reverse-agent-iteration@v2`, `samplereverse-frontier@v2` |
| execution authority | `project_state/decision_packet.md`; `task_packet.task` is derived guidance |
| current artifact | `solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json` |
| artifact freshness/source_run | `current` / `sr_lhs_hook_observation_reliability_20260524_r4` |

## Arg0 Writer Trace

| candidate_hex | actual_arg0@0x258c | preview prefix | 0x258b row | 0x2559 row | 0x253a row | nearest write | final writer |
|---|---:|---|---|---|---|---|---|
| `78d540b49c59077041414141414141` | `0x35cd018` | `46006c004464830d311c7010` | missing | missing | missing | `0x7851680e`, non-intersecting | missing |
| `5a3e7f46ddd474d041414141414141` | `0x378cfd8` | `460061357f0b8c688502de32` | missing | missing | missing | `0x7736680e`, non-intersecting | missing |
| `78d540b49c59076f41414141414141` | `0x421d018` | `d6707f3ad7f8bb0e0fd64fcb` | missing | missing | missing | `0x796c680e`, non-intersecting | missing |

## Conclusion

The current selected artifact still confirms actual compare `arg0` at `module+0x258c`, with candidate-dependent arg0 values and previews. The existing artifact does not contain separate runtime-backed rows for `module+0x258b`, `module+0x2559`, or `module+0x253a`, so this round must not claim a complete pointer chain or a final data writer.

The new projection classifies the gap as `arg0_final_writer_trace_schema_gap`. Pointer carrier, pointer write, and final data writer are now explicitly separated:

- `pointer_carrier_is_final_writer = false`
- `pointer_write_is_final_data_writer = false`
- `last_writer_candidates = []`
- `nearest_write_intersects_arg0 = false`

This is not a Base64/RC4 probe because real LHS final data-writer provenance is still missing. The next bounded evidence source is one fixed-candidate sidecar rerun using the newly emitted trace fields for `0x253a`, `0x2559`, `0x258b`, and `0x258c`.

## Code Changes

- Added `arg0_final_data_writer_trace_point` emission to the Olly/Frida sidecar observations.
- Added `arg0_final_data_writer_trace` aggregation in `CompareAwareSearchStrategy`, while keeping `last_writer_candidates` gated on real intersecting actual-arg0 writes.
- Added project_state derivation and blocker projection for the five approved arg0 final-writer states.
- Added fixture/unit coverage for pointer carrier separation, pointer writes not becoming final data writes, non-intersecting writes staying out of candidates, intersecting writes promoting only with overlap, fallback non-provenance, and old frame schema gaps.

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or pointer or writer or raw_write or provenance or classification"` | passed, `58 passed, 138 deselected` |
| `python -m pytest -q tests/test_project_state.py -k "artifact or provenance or bottleneck or decision or report or pointer or writer"` | passed, `97 passed, 41 deselected` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4` | passed; rebuilt active project_state from selected run |
| `python -m pytest -q tests/test_project_state.py` | passed, `138 passed` |
| `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed after refreshing decision state binding to rebuilt active state |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed; blocker is `arg0_final_writer_trace_schema_gap` |
| `git diff --check` | passed; Git reported line-ending normalization warnings only |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed |
| `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260525_reverse_arg0_final_data_writer_trace` | passed; created minimal archive |

## Git Diff Summary

Diff scope is limited to active `project_state` files, sidecar/schema projection code, and focused tests. No full `solve_reports` directory was added.

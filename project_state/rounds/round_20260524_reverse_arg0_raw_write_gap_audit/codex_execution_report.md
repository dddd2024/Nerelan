```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_reverse_arg0_raw_write_gap_audit",
  "round_id": "round_20260524_reverse_arg0_raw_write_gap_audit",
  "based_on_decision_id": "decision_20260524_reverse_arg0_raw_write_gap_audit",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/artifact_index.json",
    "project_state/current_state.json",
    "project_state/decision_packet.md",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "reverse_agent/project_state.py",
    "reverse_agent/strategies/compare_aware_search.py",
    "tests/test_compare_aware_search_strategy.py",
    "tests/test_project_state.py"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py",
    "python -m pytest -q tests/test_compare_aware_search_strategy.py -k \"arg0 or raw_write or last_writer or provenance or classification\"",
    "python -m pytest -q tests/test_project_state.py -k \"artifact or provenance or bottleneck or decision or report\"",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "git diff --check",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260524_reverse_arg0_raw_write_gap_audit"
  ],
  "generated_artifacts": [
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/model_gate.json",
    "project_state/task_packet.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260524_reverse_arg0_raw_write_gap_audit/round_manifest.json"
  ],
  "next_suggested_task": [
    "Run a bounded pointer-origin trace before module+0x258c actual arg0, starting with the 0x2559..0x258b ESI source window; do not run Base64/RC4 probe until runtime-backed writer provenance exists."
  ]
}
```

# CODEX_EXECUTION_REPORT

## 2026-05-24 Arg0 Raw Write Gap Audit

Result: `SUCCESS` / `ACCEPTED`.

This round stayed on `decision_20260524_reverse_arg0_raw_write_gap_audit`. It did not run a harness, Base64/RC4 probe, old solver, candidate search, or beam/budget/frontier expansion. The selected runtime evidence remains `sr_lhs_hook_observation_reliability_20260524_r4`.

## Scope Audit

| item | result |
|---|---|
| decision id | `decision_20260524_reverse_arg0_raw_write_gap_audit` |
| decision status | `APPROVED` |
| mainline | `reverse_solving` |
| skill profiles | `reverse-agent-iteration@v2`, `samplereverse-frontier@v2` |
| task_packet task | `Improve compare lhs last-writer instrumentation` is a derived suggestion |
| execution authority | `project_state/decision_packet.md` |
| current artifact | `solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json` |
| artifact freshness/source_run | `current` / `sr_lhs_hook_observation_reliability_20260524_r4` |

## Gap Evidence Table

| candidate_hex | actual_arg0 | preview prefix | nearest write | module offset | instruction | seq/thread | distance_to_arg0 | bounded reason |
|---|---:|---|---:|---|---|---|---:|---|
| `78d540b49c59077041414141414141` | `0x35cd018` | `46006c004464830d311c7010` | `0xd9dcf4` | `0x7851680e` | `mov dword ptr [ecx], eax` | `5` / `10576` | `42136352` | `write_before_arg0_window` |
| `5a3e7f46ddd474d041414141414141` | `0x378cfd8` | `460061357f0b8c688502de32` | `0xf3df24` | `0x7736680e` | `mov dword ptr [ecx], eax` | `5` / `32264` | `42266800` | `write_before_arg0_window` |
| `78d540b49c59076f41414141414141` | `0x421d018` | `d6707f3ad7f8bb0e0fd64fcb` | `0x153dec4` | `0x796c680e` | `mov dword ptr [ecx], eax` | `5` / `11928` | `47051088` | `write_before_arg0_window` |

## Classification

The 27 raw writes are real write-ring events, but they land far before the runtime compare `arg0` buffers. The current artifact has `raw_write_count=27`, `filtered_intersecting_write_count=0`, `retained_write_count=0`, and each candidate's nearest write is classified as `write_before_arg0_window`.

Audit result: no aggregation/window bug was found in the existing retained-writer path. `filteredWriteRing()` uses the static compare callsite slots and targets `arg0` from `compareSlots[1]`, which corresponds to the return-address-prefixed slot layout. The sidecar is filtering against the correct actual compare arg0 window, but the writes it observed are not the origin of that pointer.

Final blocker: `arg0_pointer_origin_untracked`.

This means the current monitor is seeing unrelated or earlier stack/object writes, while the true actual `arg0` pointer origin remains outside the observed write window. It is not appropriate to promote CompareProbe fallback to writer provenance, and it is still too early for Base64/RC4 probing.

## Code Changes

- Added `raw_write_gap_summary` generation in `reverse_agent/strategies/compare_aware_search.py`, including per-candidate actual `arg0`, nearest write, distance, bounded reason, target source, and recommended bounded hook points.
- Added compatibility derivation in `reverse_agent/project_state.py` so old current artifacts without `raw_write_gap_summary` still project `arg0_pointer_origin_untracked` from `missing_candidate_reasons`.
- Rebuilt active `project_state` from `sr_lhs_hook_observation_reliability_20260524_r4`; `current_bottleneck.blocker` is now `arg0_pointer_origin_untracked`.
- Updated focused tests for strategy and project_state projection.

## Harness And Artifacts

No harness was run. No new runtime artifact was produced. The active runtime evidence is still the current selected run `sr_lhs_hook_observation_reliability_20260524_r4`; the new fields are deterministic projections over that artifact.

## Tests

| command | result |
|---|---|
| `python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py` | passed |
| `python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or raw_write or last_writer or provenance or classification"` | passed, `43 passed, 151 deselected` |
| `python -m pytest -q tests/test_project_state.py -k "artifact or provenance or bottleneck or decision or report"` | passed, `90 passed, 46 deselected` |
| `python -m pytest -q tests/test_project_state.py` | passed, `136 passed` |
| `python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4` | passed |
| `python -m reverse_agent.project_state lint-decision --state-dir project_state` | passed |
| `python -m reverse_agent.project_state status --state-dir project_state` | passed; `missing: []`, selected run unchanged |
| `python -m reverse_agent.project_state lint-report --state-dir project_state` | passed; `lint-report: OK`, pre-archive warning only |
| `git diff --check` | passed; Git reported line-ending normalization warnings only |
| `python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260524_reverse_arg0_raw_write_gap_audit` | passed; created minimal round manifest |

## Git Diff Summary

Current diff scope is limited to active `project_state` files, the strategy/project_state projection code, and focused tests. No full `solve_reports` directory was added.

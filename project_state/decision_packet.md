# DECISION_PACKET.md

## 1. Goal

Investigate the stalled `compare_handoff_probe` path for `samplereverse` by performing a narrow backward slice from the `0x401b50` helper arguments and call-site context.

The goal is not to generate more candidates. The goal is to identify what data flows into the helper, how it relates to `[ebp-0x1170]`, and why `post_handoff_lhs_reload` at `module+0x2559` was unavailable while helper enter/return and compare lhs capture were available.

Expected output:
- A new bounded diagnostic artifact, preferably named around `helper_arg_slice` or `compare_handoff_slice`.
- Updated `project_state/*` files.
- A new `CODEX_EXECUTION_REPORT` explaining whether the helper argument slice closed the evidence gap.

## 2. Current Evidence

Current active strategy is `CompareAwareSearchStrategy`; the current mainline is `L15(prefix8)`, and the known transform chain is:

`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`

The latest best runtime candidate is still exact2:

- `candidate_hex`: `78d540b49c59077041414141414141`
- `candidate_prefix`: `78d540b49c590770`
- `runtime_ci_exact_wchars`: `2`
- `runtime_ci_distance5`: `246`
- `compare_semantics_agree`: `true`

The current frontier candidate is:

- `candidate_hex`: `5a3e7f46ddd474d041414141414141`
- `candidate_prefix`: `5a3e7f46ddd474d0`
- `runtime_ci_exact_wchars`: `1`
- `runtime_ci_distance5`: `258`
- `compare_semantics_agree`: `true`

Current bottleneck is:

- `stage`: `compare_handoff_probe`
- `reason`: `handoff_capture_partial`
- `confidence`: `medium`

Latest `compare_handoff_probe` evidence:

- `handoff_helper_rva`: `0x1b50`
- `compare_call_rva`: `0x258c`
- `lhs_slot`: `[ebp-0x1170]`
- `post_handoff_reload_rva`: `0x2559`
- `static_anchor_valid`: `true`
- `candidate_count`: `3`
- `runtime_backed_count`: `3`
- `handoff_helper_enter`: `available`
- `handoff_helper_return`: `available`
- `lhs_slot`: `available`
- `compare_lhs_buffer`: `available`
- `post_handoff_lhs_reload`: `unavailable`

Codex's previous report confirms that the helper at `module+0x1b50` is runtime-reachable for all 3 diagnostic candidates, but the planned `module+0x2559` post-reload observation did not fire. Therefore the next bounded direction is a narrower backward slice from `0x401b50` helper arguments and call-site context, not broader search.

## 3. Do Not Do

Do not:

1. Return to old `sample_solver` blind search.
2. Increase beam, budget, topN, timeout, or frontier iteration limits as the main action.
3. Use `compare_semantics_agree=false` candidates as the primary frontier.
4. Commit the full `solve_reports` directory.
5. Repeat the exact2 basin value-pool evaluation with pools:
   - `0:78`
   - `1:d5/3e/3c`
   - `2:40/7f/80`
   - `3:b4/8f`
   - `4:9c`
6. Repeat the fixed H1/H3 8-candidate prefix8 plus Base64 boundary contrast set.
7. Repeat the current 5-candidate transform trace consistency audit without new runtime evidence.
8. Repeat the same `compare_handoff_probe` hook set without narrowing the `0x401b50` helper slice.
9. Scan the entire `solve_reports` directory unless a specific artifact path is needed.

## 4. Files To Inspect

Primary code files:

1. `reverse_agent/strategies/compare_aware_search.py`
2. `reverse_agent/olly_scripts/compare_handoff_probe.py`
3. `tests/test_compare_aware_search_strategy.py`
4. `tests/test_tool_runners.py`
5. `tests/test_project_state.py`

Project state files:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`

Targeted runtime artifacts only:

1. `solve_reports\harness_runs\samplereverse_compare_handoff_probe_20260505\reports\tool_artifacts\samplereverse\compare_handoff_probe\compare_handoff_probe.json`
2. `solve_reports\harness_runs\samplereverse_compare_handoff_probe_20260505\reports\tool_artifacts\samplereverse\transform_trace_consistency\transform_trace_consistency.json`
3. `solve_reports\harness_runs\samplereverse_compare_handoff_probe_20260505\summary.json`
4. `solve_reports\harness_runs\samplereverse_compare_handoff_probe_20260505\run_manifest.json`

Only inspect other artifacts if the above files directly reference them and they are necessary for the helper argument slice.

## 5. Required Audit

Perform a narrow static and runtime audit around the helper call path.

Required audit steps:

1. Locate the call site around `module+0x253a` / `call 0x401b50`.
2. Identify the exact argument setup for helper `0x401b50`.
3. For each argument, record:
   - stack/register source
   - immediate constants
   - pointer targets
   - whether the value is candidate-dependent
   - whether the value correlates with `[ebp-0x1170]`
4. Backward-slice only the instructions necessary to explain those helper arguments.
5. Determine whether `[ebp-0x1170]` is:
   - an input buffer,
   - an output buffer,
   - a temporary decoded/encoded buffer,
   - a compare lhs staging slot,
   - or a stale stack slot from an earlier transformation stage.
6. Explain why `post_handoff_lhs_reload` at `module+0x2559` did not fire:
   - wrong address,
   - conditional path not taken,
   - instruction boundary mismatch,
   - hook placement after control-flow diversion,
   - or incorrect assumption about reload site.
7. If needed, refine hook placement by moving from semantic names to instruction-confirmed addresses.
8. Capture minimal runtime samples for the existing 3 diagnostic candidates only.
9. Compare helper-enter arguments, helper-return values, `[ebp-0x1170]`, and compare lhs buffer across the 3 candidates.
10. Produce a classification:
    - `helper_arg_slice_confirmed`
    - `helper_arg_slice_partial`
    - `wrong_reload_anchor`
    - `wrong_helper_assumption`
    - `needs_pre_rc4_base64_probe`

## 6. Implementation Scope

Allowed implementation:

1. Add a bounded diagnostic runner, for example:
   - `run_compare_handoff_slice_probe()`
   - or `run_helper_arg_slice_probe()`

2. Add a narrow Frida/UI script if needed, for example:
   - `reverse_agent/olly_scripts/compare_handoff_slice_probe.py`
   - or extend `compare_handoff_probe.py` only if the extension remains bounded and does not alter candidate generation.

3. Emit a new artifact containing:
   - helper call-site disassembly window,
   - helper argument map,
   - runtime argument captures,
   - `[ebp-0x1170]` observations,
   - compare lhs observations,
   - classification,
   - next bounded action.

4. Update project state builder to index the new artifact.

5. Add tests covering:
   - schema stability,
   - no candidate promotion,
   - no search budget expansion,
   - project_state indexing,
   - classification handling.

Not allowed:

1. Do not alter candidate ranking.
2. Do not promote new candidates from this diagnostic.
3. Do not increase search budgets.
4. Do not make this a general-purpose binary analysis pass.
5. Do not backslide to broad solve_reports scanning.

## 7. Tests

Run at minimum:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

Then run the bounded harness case:

```powershell
python -m reverse_agent.harness ^
  --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json ^
  --run-name samplereverse_helper_arg_slice_probe_20260505 ^
  --reports-dir solve_reports ^
  --analysis-mode "Auto" ^
  --model-type "Copilot CLI" ^
  --copilot-timeout-seconds 300 ^
  --ctf-skill-profile compact ^
  --case-id samplereverse-exact1-projected-vs-neighbor ^
  --no-resume
```

Then rebuild project state:

```powershell
python -m reverse_agent.project_state build ^
  --reports-dir solve_reports ^
  --sample samplereverse ^
  --run-name samplereverse_helper_arg_slice_probe_20260505

python -m reverse_agent.project_state status
```

Expected test result:

- Existing unit tests still pass.
- Harness completes 1 case with 0 errors.
- New artifact is indexed in `artifact_index.json`.
- `current_state.json` records the new classification and next bounded action.

## 8. Stop Conditions

Stop successfully if one of the following is true:

1. The helper argument slice explains the dataflow from candidate input or transformed material into `0x401b50`, `[ebp-0x1170]`, and compare lhs.
2. The investigation proves `module+0x2559` is the wrong reload anchor and proposes a corrected instruction-confirmed hook point.
3. The helper is proven not to be the missing handoff point, and the report identifies the next bounded probe target.
4. The result produces a new runtime-backed classification that is more informative than `handoff_capture_partial`.

Stop and report blockage if:

1. Required runtime artifact paths are missing.
2. Hook execution becomes non-deterministic across the same 3 candidates.
3. The script cannot reliably capture helper arguments.
4. The only apparent next step is broader candidate search or budget expansion.

Final report must include:

1. What was inspected.
2. What changed.
3. What did not change.
4. Runtime evidence summary.
5. Whether the next step is:
   - refined helper hook,
   - corrected reload anchor,
   - pre-RC4/Base64 dynamic probe,
   - or return to compare-aware candidate refinement.

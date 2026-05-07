# DECISION_PACKET.md

## 1. Goal

Resolve the current `producer_trace_inconclusive` bottleneck for `samplereverse`.

The immediate goal is to determine whether the known transform chain:

`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`

is still runtime-consistent at the material-buffer level, because the previous producer trace reached candidate-dependent producer-side buffers but did not reach the expected static compare path.

This round must not expand candidate search. It must either:

1. capture bounded pre-RC4/Base64/RC4 runtime materials and verify the transform chain, or
2. if a precise instruction target is obvious from the captured `0x233d` context, add one narrower producer hook and close where `producer.eax` / `producer.lhs_slot` flows next.

Preferred direction: bounded pre-RC4/Base64 material capture.

Expected output:

- A new bounded diagnostic artifact, preferably named:
  - `pre_rc4_material_probe.json`
  - or `base64_rc4_material_probe.json`
- Updated `project_state/*`
- New `CODEX_EXECUTION_REPORT.md`
- No candidate promotion
- No ranking change
- No search-budget expansion

## 2. Current Evidence

Current active strategy:

- `CompareAwareSearchStrategy`

Current mainline:

- `L15(prefix8)`

Known transform chain:

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

Current best exact2 candidate:

```text
candidate_hex: 78d540b49c59077041414141414141
candidate_prefix: 78d540b49c590770
compare_semantics_agree: true
runtime_ci_exact_wchars: 2
runtime_ci_distance5: 246
source: pairscan
```

Current frontier candidate:

```text
candidate_hex: 5a3e7f46ddd474d041414141414141
candidate_prefix: 5a3e7f46ddd474d0
compare_semantics_agree: true
runtime_ci_exact_wchars: 1
runtime_ci_distance5: 258
source: exact2_seed(78d540b49c590770) -> refine(seed) -> guided(frontier)
```

Latest bottleneck:

```text
stage: compare_producer_trace_probe
reason: producer_trace_inconclusive
confidence: medium
```

Latest Codex run:

```text
run_name: samplereverse_compare_producer_trace_probe_20260507_rerun2
status: completed, 1 case, 0 errors
classification: producer_trace_inconclusive
runtime-backed candidates: 3
tests: 180 passed
```

Important findings from latest producer trace:

1. Runtime reached:
   - `module+0x233d`
   - `module+0x253a`
   - `module+0x2554`

2. Runtime did not reach:
   - `module+0x2559`
   - `module+0x258b`
   - `module+0x258c`
   - `module+0x1028ac` / `0x5028ac`

3. Hook miss classification:

```text
control-flow skipped
```

4. Candidate-dependent fields were observed:

```text
producer.eax_preview_hex: candidate-dependent
producer.lhs_slot_preview_hex: candidate-dependent
```

5. No relation was closed between producer-side candidate-dependent data and compare helper args because compare entry/call args were not observed.

6. Best candidate did not improve:

```text
exact2 remains 78d540b49c59077041414141414141
runtime_ci_exact_wchars=2
runtime_ci_distance5=246
```

Therefore the next bounded action is:

```text
capture pre-RC4/Base64 runtime materials, or choose a narrower producer hook from captured 0x233d context if one instruction-confirmed target is obvious
```

## 3. Do Not Do

Do not:

1. Return to old `sample_solver` blind search.
2. Increase beam, budget, topN, timeout, or frontier iteration limits.
3. Use `compare_semantics_agree=false` candidates as the primary frontier.
4. Commit the full `solve_reports` directory.
5. Repeat exact2 basin value-pool evaluation.
6. Repeat the fixed H1/H3 8-candidate prefix8 boundary contrast set.
7. Repeat the current 5-candidate transform trace consistency audit without new runtime evidence.
8. Repeat `compare_producer_trace_probe` without using its `producer_trace_inconclusive` classification.
9. Repeat the same static compare path assumption `0x2559 -> 0x258b -> 0x258c -> 0x1028ac` as the primary route unless runtime evidence shows it is reached.
10. Generate new candidate pools.
11. Expand search while material-buffer evidence remains unresolved.
12. Scan the full `solve_reports` tree.

## 4. Files To Inspect

Primary project state files:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`

Primary implementation files:

1. `reverse_agent/strategies/compare_aware_search.py`
2. `reverse_agent/project_state.py`
3. `tests/test_compare_aware_search_strategy.py`
4. `tests/test_tool_runners.py`
5. `tests/test_project_state.py`

Relevant previous diagnostic scripts:

1. `reverse_agent/olly_scripts/compare_producer_trace_probe.py`
2. Any existing pre-RC4/Base64 or transform-trace diagnostic script if present

Targeted artifacts only:

1. `solve_reports\harness_runs\samplereverse_compare_producer_trace_probe_20260507_rerun2\reports\tool_artifacts\samplereverse\compare_producer_trace_probe\compare_producer_trace_probe.json`
2. `solve_reports\harness_runs\samplereverse_compare_producer_trace_probe_20260507_rerun2\reports\tool_artifacts\samplereverse\transform_trace_consistency\transform_trace_consistency.json`
3. `solve_reports\harness_runs\samplereverse_compare_producer_trace_probe_20260507_rerun2\reports\tool_artifacts\samplereverse\samplereverse_compare_probe.json`
4. `solve_reports\harness_runs\samplereverse_compare_producer_trace_probe_20260507_rerun2\summary.json`
5. `solve_reports\harness_runs\samplereverse_compare_producer_trace_probe_20260507_rerun2\run_manifest.json`

Only inspect additional artifacts if these files directly reference them.

## 5. Required Audit

### A. Material-stage runtime capture

Implement a bounded diagnostic that captures runtime material buffers across the known transform chain.

Use the same 3 diagnostic candidates only:

```text
78d540b49c59077041414141414141
78d540b49c59077040414141414141
5a3e7f46ddd474d041414141414141
```

For each candidate, capture:

1. Original input bytes.
2. UTF-16LE material buffer:
   - pointer
   - length if available
   - hex preview
   - decoded preview if valid
3. Base64 input buffer:
   - pointer
   - length if available
   - hex preview
   - ASCII/UTF-16LE preview if valid
4. Base64 output buffer:
   - pointer
   - length if available
   - hex preview
   - ASCII preview if valid
5. RC4 key material if statically/runtimely available.
6. RC4 input buffer:
   - pointer
   - length if available
   - hex preview
7. RC4 output buffer:
   - pointer
   - length if available
   - hex preview
   - UTF-16LE preview if valid
8. Producer-side buffer already seen in previous run:
   - `producer.eax_preview_hex`
   - `producer.lhs_slot_preview_hex`
9. Whether RC4 output matches or is a prefix/slice/encoding of:
   - `producer.eax_preview_hex`
   - `producer.lhs_slot_preview_hex`
   - `[ebp-0x1170]` preview
   - any later observed candidate-dependent local slot

Required relation table:

| candidate | utf16 material | base64 output | rc4 output | producer.eax | producer.lhs_slot | rc4->producer relation |
|---|---|---|---|---|---|---|

The core question:

```text
Does the runtime RC4 output equal the candidate-dependent producer-side buffer?
```

### B. Runtime/offline transform agreement check

For each of the 3 candidates, compare captured runtime materials with offline-computed materials.

Required fields:

1. `offline_utf16_hex`
2. `runtime_utf16_hex`
3. `utf16_agree`
4. `offline_base64_ascii`
5. `runtime_base64_ascii`
6. `base64_agree`
7. `offline_rc4_hex`
8. `runtime_rc4_hex`
9. `rc4_agree`
10. `first_divergence_stage`

Allowed classifications:

```text
material_chain_agrees
utf16_diverges
base64_diverges
rc4_diverges
material_capture_partial
material_capture_unreliable
```

If the material chain agrees, Codex must not keep debugging UTF-16LE/Base64/RC4; it must move to compare-path discovery.

If the material chain diverges, Codex must identify the first divergent stage and stop before candidate search.

### C. Minimal producer-side continuation check

Only if Codex can identify one precise instruction-confirmed target from the previous `0x233d` producer window, it may add a narrow hook after `0x233d`.

Use the captured producer window:

```text
module+0x2310..0x2365
```

Candidate targets should be selected only if they write, copy, transform, or consume:

- `eax`
- `[ebp-0x1170]`
- `[ebp-0x116c]`
- `[ebp-0x1168]`
- the slot that previously yielded `producer.lhs_slot_preview_hex`

Required output if this branch is used:

1. instruction address
2. instruction bytes
3. decoded instruction
4. why this is the next producer target
5. register and memory previews before/after the instruction
6. whether it explains why `0x2559`, `0x258b`, `0x258c`, and `0x1028ac` were skipped

Do not add more than 3 new hook addresses in this branch.

### D. Compare-path consequence audit

If material capture proves that RC4 output already matches `producer.eax` or `producer.lhs_slot`, then Codex must classify the compare issue as a path-discovery problem.

Required output:

1. Which runtime buffer contains the transformed candidate.
2. Whether the expected static compare path is skipped for all 3 diagnostic candidates.
3. Whether the program likely uses:
   - alternate compare path,
   - early rejection path,
   - delayed compare path,
   - wrapper compare path,
   - or transformed-buffer staging before compare.
4. Next narrower target.

## 6. Implementation Scope

Allowed:

1. Add one bounded diagnostic script, preferably:

```text
reverse_agent/olly_scripts/pre_rc4_material_probe.py
```

Alternative acceptable names:

```text
reverse_agent/olly_scripts/base64_rc4_material_probe.py
reverse_agent/olly_scripts/transform_material_probe.py
```

2. Add one strategy runner, for example:

```python
run_pre_rc4_material_probe()
```

3. Add one artifact name constant, for example:

```python
PRE_RC4_MATERIAL_PROBE_FILE_NAME
```

4. Emit one compact artifact:

```text
pre_rc4_material_probe.json
```

5. Artifact must include:

- material capture table
- offline/runtime transform agreement table
- candidate-dependent material relation table
- first divergence stage
- final classification
- next bounded action

6. Update project state builder to index the new artifact.

7. Add tests for:

- schema stability
- artifact indexing
- no candidate promotion
- no ranking change
- no budget expansion
- classification handling
- surrogate-safe JSON output if decoded material contains invalid Unicode

Not allowed:

1. Do not modify ranking.
2. Do not promote candidates.
3. Do not generate new candidates.
4. Do not increase budget, beam, topN, timeout, or frontier iteration limits.
5. Do not introduce a broad dynamic tracer.
6. Do not scan the full `solve_reports` tree.
7. Do not repeat `compare_producer_trace_probe` as-is.
8. Do not debug old `0x401b50 -> 0x2559` assumption again.
9. Do not continue candidate refinement unless material-chain agreement and compare-path relation are clear.

## 7. Tests

Run unit tests:

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

Then run the bounded harness case with a new run name:

```powershell
python -m reverse_agent.harness ^
  --dataset .\samplereverse_exact1_projected_vs_neighbor_20260424.json ^
  --run-name samplereverse_pre_rc4_material_probe_20260507 ^
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
  --run-name samplereverse_pre_rc4_material_probe_20260507

python -m reverse_agent.project_state status
```

Expected result:

1. Unit tests pass.
2. Harness completes 1 case with 0 errors.
3. New artifact is indexed.
4. `current_state.json` no longer only reports `producer_trace_inconclusive`.
5. `codex_execution_report.md` explains:
   - what material buffers were captured,
   - whether offline/runtime UTF-16LE agree,
   - whether offline/runtime Base64 agree,
   - whether offline/runtime RC4 agree,
   - whether RC4 output maps to producer-side candidate-dependent data,
   - whether the next target is compare-path discovery or transform-stage correction.

## 8. Stop Conditions

Stop successfully if one of these is true:

1. Runtime UTF-16LE/Base64/RC4 materials are captured for all 3 candidates.
2. The first divergent transform stage is identified.
3. Runtime RC4 output is shown to match `producer.eax` or `producer.lhs_slot`.
4. Runtime RC4 output is shown not to match producer-side candidate-dependent buffers, with a clear first mismatch.
5. The material chain agrees and the remaining issue is classified as compare-path discovery.
6. A narrower producer continuation target is identified from `0x233d` context with runtime evidence.

Stop and report blockage if:

1. Material buffers cannot be captured reliably.
2. Runtime hooks behave nondeterministically across the same 3 candidates.
3. Captured material contains ambiguous or invalid previews that cannot be compared safely.
4. No transform stage can be validated.
5. The only apparent next action is broad tracing or larger candidate search.
6. Required artifacts are missing.

Final `CODEX_EXECUTION_REPORT.md` must include:

1. What was inspected.
2. What changed.
3. What did not change.
4. Material hook availability table.
5. Offline/runtime transform agreement table.
6. Candidate-dependent producer relation table.
7. First divergence stage.
8. Final classification, one of:

```text
material_chain_agrees
utf16_diverges
base64_diverges
rc4_diverges
rc4_matches_producer_buffer
rc4_not_producer_buffer
needs_compare_path_discovery
needs_narrower_producer_hook
material_capture_partial
material_capture_unreliable
```

9. Recommended next bounded action.

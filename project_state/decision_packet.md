# DECISION_PACKET.md

## 1. Goal

Resolve the current `wrong_helper_assumption` bottleneck for `samplereverse`.

The immediate goal is to identify the real candidate-dependent data producer or handoff path before the wide `flag{` compare.

The previous round proved that the observed `0x401b50` helper is not the missing post-helper handoff into `module+0x2559`. Therefore this round must move one step earlier or later in the local dataflow, instead of repeating the same helper return-site audit.

Expected outcome:

1. Identify the true pre-compare producer of the buffer later compared against `flag{`.
2. Determine whether the compare call at `0x5028ac` is reached through a different caller path, delayed path, or wrapper.
3. Capture runtime stack arguments at the actual compare helper entry, not only at the static call-site `module+0x258c`.
4. Produce one new bounded diagnostic artifact.
5. Update `project_state/*` and `CODEX_EXECUTION_REPORT.md`.

This round must not generate new candidate pools, promote candidates, or increase search budgets.

## 2. Current Evidence

Current active strategy:

- `CompareAwareSearchStrategy`

Known transform chain:

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

Current mainline:

```text
L15(prefix8)
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
stage: compare_handoff_return_site_probe
reason: wrong_helper_assumption
confidence: medium
```

Latest return-site probe findings:

- `handoff_helper_enter`: available
- `handoff_helper_return`: available
- `helper_return_site`: available
- `lhs_slot`: available
- `post_handoff_lhs_reload`: unavailable
- `post_handoff_after_reload`: unavailable
- `pre_compare_push_esi`: unavailable
- `wide_flag_prefix_compare`: unavailable
- `compare_call_args`: unavailable

Critical finding:

```text
helper return address = module+0x233d for all 3 diagnostic candidates
helper return address != module+0x2559
```

Therefore:

```text
0x401b50 is not the missing handoff into module+0x2559.
```

The next bounded action from current state is:

```text
move to the next bounded pre-compare handoff target
```

Artifact index confirms the latest run and artifact references are already present, with no missing indexed artifacts.

## 3. Do Not Do

Do not:

1. Return to old `sample_solver` blind search.
2. Increase beam, budget, topN, timeout, or frontier iteration limits.
3. Use `compare_semantics_agree=false` candidates as the primary frontier.
4. Commit the full `solve_reports` directory.
5. Repeat exact2 basin value-pool evaluation.
6. Repeat the fixed H1/H3 8-candidate prefix8 boundary contrast set.
7. Repeat the current 5-candidate transform trace consistency audit without new runtime evidence.
8. Repeat `compare_handoff_return_site_probe` without using its `wrong_helper_assumption` classification.
9. Scan the full `solve_reports` tree.
10. Generate new candidate pools before the compare-side dataflow is identified.

These constraints are already recorded in `negative_results.json`, including hard blocks on `compare_semantics_agree=false` as primary frontier and committing full `solve_reports`.

## 4. Files To Inspect

Primary project files:

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

Relevant previous diagnostic script:

1. `reverse_agent/olly_scripts/compare_handoff_return_site_probe.py`

Targeted artifacts only:

1. `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\reports\tool_artifacts\samplereverse\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json`
2. `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\reports\tool_artifacts\samplereverse\transform_trace_consistency\transform_trace_consistency.json`
3. `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\reports\tool_artifacts\samplereverse\samplereverse_compare_probe.json`
4. `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\summary.json`
5. `solve_reports\harness_runs\samplereverse_compare_return_site_probe_20260507\run_manifest.json`

Only inspect other artifacts if these files directly reference them.

## 5. Required Audit

### A. Local control-flow audit around `module+0x233d`

The previous round showed the helper returns to `module+0x233d`, not `module+0x2559`.

Codex must inspect the static and runtime context around `module+0x233d`.

Required output:

1. Bytes and decoded instructions around:
   - `module+0x2310` through `module+0x2365`
   - any local calls immediately before and after `module+0x233d`
2. Register state at `module+0x233d`:
   - `eax`
   - `esi`
   - `edi`
   - `ecx`
   - `edx`
   - `ebp`
   - `esp`
3. Stack preview at `esp`.
4. Local frame preview around:
   - `[ebp-0x1170]`
   - `[ebp-0x116c]`
   - `[ebp-0x1168]`
   - nearby candidate-buffer slots if statically visible
5. Memory previews at:
   - `eax`
   - `esi`
   - `edi`
   - `[ebp-0x1170]`
6. Whether any of those previews are candidate-dependent across the same 3 diagnostic candidates.

The goal is to determine what `module+0x233d` actually does after `0x401b50` returns.

### B. Actual compare-helper entry audit

The previous probe failed to capture `wide_flag_prefix_compare` and compare-call stack arguments at `module+0x258c`.

Instead of only hooking the static call-site, Codex must hook the compare helper entry itself:

```text
0x5028ac
```

Required runtime capture at compare helper entry:

1. Caller return address.
2. Caller module offset.
3. `esp`.
4. `[esp+0x00]`, `[esp+0x04]`, `[esp+0x08]`, `[esp+0x0c]`.
5. Memory previews for pointer-looking stack values.
6. UTF-16LE decoded previews when valid.
7. Whether either side contains or points to `flag{`.
8. Whether either side is candidate-dependent.
9. Whether any side matches:
   - `eax` at `module+0x233d`
   - `esi` at `module+0x233d`
   - `[ebp-0x1170]`
   - previous `helper_return.eax`
   - previous `helper_return.lhs_slot`

Important: do not assume the static call-site stack layout is correct. The previous run did not capture compare args at `module+0x258c`, so the real compare entry may be reached through a wrapper, alternate caller, or delayed path.

### C. Candidate-dependent buffer producer audit

Codex must identify which local value becomes candidate-dependent immediately before compare.

Use the same 3 diagnostic candidates:

```text
78d540b49c59077041414141414141
78d540b49c59077040414141414141
5a3e7f46ddd474d041414141414141
```

For each candidate, record a compact table:

| hook point | eax preview | esi preview | edi preview | [ebp-0x1170] preview | candidate-dependent? | relation to compare arg |
|---|---|---|---|---|---|---|

Minimum hook points:

1. `module+0x233d`
2. any confirmed instruction boundary after `module+0x233d` that writes or reloads candidate buffer pointers
3. `module+0x253a`
4. `module+0x2554`
5. `module+0x2559`
6. `module+0x258b`
7. compare helper entry `0x5028ac`

If hooks at `0x2559`, `0x258b`, or `0x258c` still do not fire, Codex must classify why:

1. control-flow skipped,
2. wrong module base,
3. path exits earlier,
4. wrapper/alternate compare path,
5. hook placement invalid,
6. anti-debug/timing issue,
7. static assumption stale.

### D. Bounded fallback: pre-RC4/Base64 material capture

Only if A-C fail to identify the compare-side dataflow, Codex may run a bounded pre-RC4/Base64 material probe.

This fallback must not become a broad tracer.

Allowed fallback target:

```text
capture pre-RC4/Base64 runtime buffers with the same 3 diagnostic candidates
```

Required output:

1. UTF-16LE input buffer preview.
2. Base64 output buffer preview.
3. RC4 input buffer preview.
4. RC4 output buffer preview.
5. Relation between RC4 output and the eventual compare argument if capturable.

## 6. Implementation Scope

Allowed:

1. Add one bounded diagnostic script, preferably:

```text
reverse_agent/olly_scripts/compare_producer_trace_probe.py
```

Alternative acceptable names:

```text
reverse_agent/olly_scripts/pre_compare_producer_probe.py
reverse_agent/olly_scripts/actual_compare_entry_probe.py
```

2. Add one strategy runner, for example:

```python
run_compare_producer_trace_probe()
```

3. Add one artifact name constant, for example:

```python
COMPARE_PRODUCER_TRACE_PROBE_FILE_NAME
```

4. Emit one compact artifact:

```text
compare_producer_trace_probe.json
```

5. Artifact must include:

- static instruction window around `module+0x233d`
- runtime table for the 3 candidates
- compare helper entry table
- candidate-dependent field summary
- relation counts
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

Not allowed:

1. Do not modify ranking.
2. Do not promote candidates.
3. Do not generate new candidates.
4. Do not increase budget, beam, topN, timeout, or frontier iteration limits.
5. Do not introduce a broad dynamic tracer.
6. Do not scan the full `solve_reports` tree.
7. Do not repeat `compare_handoff_return_site_probe` as-is.
8. Do not treat `0x401b50` as the missing handoff unless new evidence proves it.

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
  --run-name samplereverse_compare_producer_trace_probe_20260507 ^
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
  --run-name samplereverse_compare_producer_trace_probe_20260507

python -m reverse_agent.project_state status
```

Expected result:

1. Unit tests pass.
2. Harness completes 1 case with 0 errors.
3. New artifact is indexed.
4. `current_state.json` no longer only reports `wrong_helper_assumption`.
5. `codex_execution_report.md` explains:
   - what was captured,
   - which compare-side argument is candidate-dependent,
   - whether compare helper entry was observed,
   - whether the next step should be targeted candidate refinement or another bounded producer probe.

## 8. Stop Conditions

Stop successfully if one of these is true:

1. The real candidate-dependent compare argument is identified.
2. The compare helper entry is captured and its caller path is identified.
3. The relation from `module+0x233d` to the eventual compare argument is closed.
4. The reason `module+0x258c` did not capture stack args is explained.
5. A new, narrower producer or handoff target is identified with runtime evidence.
6. Pre-RC4/Base64 buffer capture proves where offline and runtime traces diverge.

Stop and report blockage if:

1. Compare helper entry `0x5028ac` cannot be reached or hooked reliably.
2. Runtime hooks behave nondeterministically across the same 3 candidates.
3. No candidate-dependent buffer can be observed after `module+0x233d`.
4. The only apparent next action is broad tracing or larger candidate search.
5. Required artifacts are missing.

Final `CODEX_EXECUTION_REPORT.md` must include:

1. What was inspected.
2. What changed.
3. What did not change.
4. Hook availability table.
5. `module+0x233d` runtime context table.
6. Actual compare helper entry argument table.
7. Candidate-dependent buffer relation table.
8. Final classification, one of:

```text
compare_entry_captured
compare_args_identified
producer_path_identified
wrong_compare_callsite
wrong_module_anchor
needs_pre_rc4_base64_probe
producer_trace_inconclusive
```

9. Recommended next bounded action.

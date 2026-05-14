# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

Investigate the candidate-dependent upstream writer path discovered by `compare_lhs_upstream_writer_audit`, and determine whether the data observed around `module+0x2312` actually feeds the transform chain that later reaches the wide compare LHS.

The next round should not expand candidate search. It should produce a bounded runtime/static audit that answers one question:

> Does the candidate-dependent UTF-16LE-looking material at `[ebp-0x1168] / edx` around `0x2312` flow through `0x2320 / 0x2325 / 0x233d / 0x2346` into the final compare LHS, or is it only upstream context unrelated to the compare buffer?

Expected output artifact: a new bounded audit artifact, preferably named along the lines of:

`compare_upstream_transform_slice_audit.json`

or, if an equivalent sidecar already exists, extend that existing sidecar instead of creating a duplicate.

## 2. Current Evidence

Current active strategy is `CompareAwareSearchStrategy`.

Current best candidate remains:

- exact2 candidate:
  - `78d540b49c59077041414141414141`
  - prefix: `78d540b49c590770`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`

Current frontier / exact1 candidate remains:

- `5a3e7f46ddd474d041414141414141`
- prefix: `5a3e7f46ddd474d0`
- runtime exact wchar count: `1`
- runtime distance5: `258`

Known transform hypothesis is still:

`input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`

Latest bottleneck:

- stage: `compare_lhs_upstream_writer_audit`
- reason: `candidate_dependent_upstream_observed`
- confidence: medium

Important latest runtime evidence:

- `producer_window_entry` at `module+0x2312`
  - instruction: `sub eax, dword ptr [edx - 4]`
  - hookable: true
  - instruction_confirmed: true
  - runtime_backed_count: 3
  - candidate_dependent: true
  - candidate-dependent fields include:
    - `[ebp-0x1168]`
    - `[ebp-0x1170]`
    - `edi`
    - `edx`
  - sample `edx` / `[ebp-0x1168]` values look like UTF-16LE expansion of the candidate bytes.
  - However:
    - `connects_to_compare_lhs: false`
    - `connects_to_lhs_store: false`
    - `compare_arg_match_count: 0`
    - `lhs_store_match_count: 0`

Prior handoff evidence:

- `compare_handoff_return_site_probe` classified the previous assumption as `wrong_helper_assumption`.
- `0x401b50` did not return to the expected `module+0x2559` path.
- Runtime evidence instead showed `helper_enter_return_is_0x233d`.
- Therefore, do not keep treating the old `0x401b50 -> 0x2559` assumption as valid.

Static discovery evidence:

- Compare-side hookable points exist around:
  - `module+0x2559`
  - `module+0x1b50`
- But Base64 / RC4 / encrypted-constant / UTF-16LE construction hooks are not instruction-confirmed.
- `breakpoint_probe_allowed` remains false.

Latest artifact index points to:

- latest harness run:
  - `sr_lhs_upstream_writer_20260514_r1`
- latest core artifact:
  - `compare_lhs_upstream_writer_audit.json`
- latest project_state was generated at `2026-05-14T14:17:12Z`.

## 3. Do Not Do

Do not do any of the following:

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam, budget, timeout, topN, or candidate pool size.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit the full `solve_reports` directory.
5. Do not repeat the exact2 basin value-pool evaluation.
6. Do not repeat the H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat the current transform trace consistency audit without new runtime evidence.
8. Do not rerun Base64/RC4 breakpoint probe before confirming an instruction-level material hook.
9. Do not repeat compare return-site audit without using its `wrong_helper_assumption` classification.
10. Do not repeat producer material confirmation unless adding new instruction-level evidence.
11. Do not expand compare-aware search instead of following upstream writer evidence.
12. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic/runtime evidence.
13. Do not scan full `solve_reports` unless a specific artifact is required.

## 4. Files To Inspect

First inspect project state:

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

Then inspect code, but avoid duplicating existing sidecars:

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Search for existing related sidecars before adding a new one:

- `compare_lhs_upstream_writer_audit`
- `compare_lhs_producer_audit`
- `material_hook_runtime_validation`
- `compare_pre_compare_handoff_target_probe`
- `compare_handoff_return_site_probe`

If an existing sidecar already covers the intended scope, extend it narrowly instead of creating another parallel mechanism.

Targeted artifacts only:

- `compare_lhs_upstream_writer_audit.json`
- `compare_handoff_return_site_probe.json`
- `function_semantic_audit.json`
- `base64_rc4_static_point_discovery.json`

Do not load the full `solve_reports` tree.

## 5. Required Audit

Implement or extend a bounded audit that covers the static/runtime slice around these offsets:

- `module+0x2312`
- `module+0x2320`
- `module+0x2325`
- `module+0x233d`
- `module+0x2346`
- final compare-side reference points:
  - `module+0x253a`
  - `module+0x2559`
  - `module+0x258b`
  - `module+0x258c`

The audit must answer:

### A. Static slice question

For the bounded region around `0x2312..0x2346`, identify:

- instruction boundaries
- calls and return sites
- stack slots read/written
- registers carrying candidate-dependent pointers
- whether `[ebp-0x1168]` is merely UTF-16LE input or a true transform-chain source
- whether `[ebp-0x1170]` is code/garbage, stale pointer, or later compare material

### B. Runtime hook question

Use only the fixed existing candidate set. At minimum include:

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

Do not generate new candidates.

For each hook point, collect:

- hit count
- instruction boundary status
- register previews:
  - eax
  - ecx
  - edx
  - esi
  - edi
  - esp / ebp if needed for frame validation
- stack slot previews:
  - `[ebp-0x1168]`
  - `[ebp-0x116c]`
  - `[ebp-0x1170]`
- pointer readability
- UTF-16LE-likeness
- Base64-likeness
- candidate dependence
- relation to final compare LHS pointer/value

### C. Dataflow classification

The artifact should classify the result as one of:

- `transform_material_confirmed`
- `candidate_dependent_but_not_compare_lhs`
- `upstream_context_only`
- `hook_unreached`
- `instruction_boundary_invalid`
- `inconclusive`

Required top-level fields:

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `candidate_dependent_points`
- `compare_lhs_connected_points`
- `validated_transform_material_points`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` must remain false unless the audit proves an instruction-confirmed, runtime-backed, candidate-dependent transform material point that plausibly feeds the final compare LHS.

### D. Failure diagnosis

If `0x2320`, `0x2325`, `0x233d`, or `0x2346` do not hit, the audit must explicitly distinguish:

- wrong hook address
- inside-instruction hook
- ASLR/base mismatch
- path not reached for the fixed candidates
- child runtime timeout/hang
- unreadable pointer
- UI/runtime launch failure

Do not silently classify missing hooks as negative semantic evidence unless the runtime was valid.

## 6. Implementation Scope

Allowed:

- Add one bounded sidecar if no equivalent exists.
- Extend existing `CompareAwareSearchStrategy` scheduling only enough to run this sidecar after `compare_lhs_upstream_writer_audit`.
- Add a thin runtime script under `reverse_agent/olly_scripts/` if needed.
- Add project_state indexing for the new artifact.
- Add negative-cache entries so rejected/inconclusive results do not trigger search expansion or Base64/RC4 probing.
- Add tests for:
  - artifact schema
  - fixed candidate set
  - no candidate generation
  - breakpoint gate remains blocked unless transform material is confirmed
  - project_state indexing

Not allowed:

- no candidate search expansion
- no new solver/ranker
- no full solve_reports commit
- no broad disassembly scan
- no Base64/RC4 breakpoint probe unless this audit produces an ACCEPT-equivalent result

## 7. Tests

Run at minimum:

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

If a new olly script is added:

```bat
python -m py_compile reverse_agent\olly_scripts\<new_script>.py
```

Targeted tests:

```bat
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

Full tests:

```bat
python -m pytest -q
```

Runtime validation, using the existing samplereverse dataset if available locally:

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_upstream_transform_slice_20260514_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Then rebuild state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_upstream_transform_slice_20260514_r1
python -m reverse_agent.project_state status
```

## 8. Stop Conditions

Stop and report if any of the following happens:

1. The new audit proves `transform_material_confirmed`.
   - Report the exact hook offset.
   - Report why it is candidate-dependent.
   - Report how it connects to compare LHS.
   - Only then allow the next round to consider Base64/RC4 breakpoint probing.

2. The new audit proves `candidate_dependent_but_not_compare_lhs` or `upstream_context_only`.
   - Keep Base64/RC4 probing blocked.
   - Report the next earlier/later bounded slice to inspect.

3. Runtime hooks do not hit.
   - Do not infer semantics.
   - Report whether this is hook-address, instruction-boundary, path, timeout, or runtime-launch failure.

4. The implementation requires scanning full `solve_reports` or expanding candidate search.
   - Stop and report why that would violate the current project_state constraints.

5. Tests fail.
   - Stop after collecting failure output.
   - Do not proceed to harness run until unit failures are resolved.

本轮核心判断：下一步不是找更多候选，而是让 Codex 把 `0x2312` 附近已经出现的候选相关 UTF-16LE 材料追到 `0x233d/0x2346` 和最终 compare LHS；追得上，才有资格进入 Base64/RC4 breakpoint；追不上，就把它标成 upstream context，不再围着它打转。

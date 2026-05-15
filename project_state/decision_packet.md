# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

修正当前 `compare_callsite_reanchor_and_lhs_provenance_audit` 的真实 compare 入口覆盖问题。

当前瓶颈不是候选搜索不足，而是实际 compare 入口没有被稳定观测：最新 r5 结果中 `actual_compare.entry_status = rejected`、`observed_count = 0`、`lhs_side = unknown`、`flag_side = unknown`，因此不能继续信任旧 `[ebp-0x1170]` anchor，也不能放开 Base64/RC4 breakpoint probe。

本轮目标：在不扩展候选搜索的前提下，增加或修正一个 bounded compare-entry / callsite argument capture probe，使 Codex 能确认：

1. `module+0x258c call 0x5028ac` 是否真的执行；
2. callsite 前 `push esi` 与 `push 0x551c4c` 是否能直接捕获 compare 两侧参数；
3. compare callee entry 是否因为 attach 地址、模块基址、导入/跳板、调用约定或位宽问题导致未命中；
4. 哪一侧是 candidate-dependent lhs，哪一侧是 flag prefix constant。

Expected output artifact: reuse or extend `compare_callsite_reanchor_and_lhs_provenance_audit.json`, or add one bounded artifact named along the lines of:

`compare_actual_callsite_argument_capture.json`

Do not create a broad duplicate audit if the current sidecar can be narrowly extended.

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

- stage: `compare_callsite_reanchor_and_lhs_provenance_audit`
- reason: `inconclusive`
- confidence: medium

Latest r5 audit evidence:

- `classification`: `inconclusive`
- `candidate_count`: `3`
- `runtime_backed_count`: `3`
- `actual_compare.entry`: `0x1028ac`
- `actual_compare.entry_status`: `rejected`
- `actual_compare.observed_count`: `0`
- `actual_compare.lhs_side`: `unknown`
- `actual_compare.flag_side`: `unknown`
- `frame_anchor.old_slot_ebp_minus_1170_status`: `inconclusive`
- `breakpoint_probe_allowed`: `false`

Important correction from the latest Codex run:

- The first implementation incorrectly treated a three-candidate run as actual compare confirmation even when only upstream hooks fired.
- The classifier now correctly requires actual compare entry observations before reporting re-anchor success.
- Therefore, the next task is not to rerun the same audit unchanged; it must improve actual compare hook coverage or capture arguments at the callsite before callee entry.

Static compare window from the current state:

- `module+0x253a`: `mov dword ptr [ebp - 0x1170], eax`
- `module+0x2554`: `call 0x401b50`
- `module+0x2559`: `mov esi, dword ptr [ebp - 0x1170]`
- `module+0x2584`: `push 5`
- `module+0x2586`: `push 0x551c4c`
- `module+0x258b`: `push esi`
- `module+0x258c`: `call 0x5028ac`

This means that even if the callee entry hook at `0x5028ac` or `module+0x1028ac` fails, the callsite should expose compare arguments immediately before the call.

Current script situation:

- `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py` is only a thin entry point that imports `main` from `compare_pre_compare_handoff_target_probe.py`.
- Actual Frida/UIA collection logic is in `compare_pre_compare_handoff_target_probe.py`.
- That script already has `compareEntrySlots(sp, moduleBase)`, but it only applies compare-argument interpretation when the hook name is `compare_helper_entry`.
- Because `compare_helper_entry` did not observe hits in r5, this round should add direct callsite-level argument capture.

## 3. Do Not Do

Do not do any of the following:

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam, budget, timeout, topN, or candidate pool size.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit the full `solve_reports` directory.
5. Do not repeat the exact2 basin value-pool evaluation.
6. Do not repeat the H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat the current transform trace consistency audit without new runtime evidence.
8. Do not rerun Base64/RC4 breakpoint probe before confirming a runtime-backed lhs producer connected to compare lhs.
9. Do not repeat compare return-site audit without using its `wrong_helper_assumption` classification.
10. Do not repeat producer material confirmation unless adding new instruction-level evidence.
11. Do not reuse old `[ebp-0x1170]` frame anchor without actual compare re-anchor evidence.
12. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic/runtime evidence.
13. Do not scan full `solve_reports` unless a specific artifact is required.

## 4. Files To Inspect

First inspect project state:

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

Then inspect code:

- `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py`
- `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py`
- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Targeted artifacts only:

- `solve_reports\harness_runs\sr_callsite_reanchor_20260514_r5\reports\tool_artifacts\samplereverse_patched\compare_callsite_reanchor_and_lhs_provenance_audit\compare_callsite_reanchor_and_lhs_provenance_audit.json`
- `solve_reports\harness_runs\sr_callsite_reanchor_20260514_r5\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.json`
- `solve_reports\harness_runs\sr_callsite_reanchor_20260514_r5\summary.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json`

Do not load the full `solve_reports` tree.

## 5. Required Audit

Codex must audit before modifying search logic.

### A. Compare entry address audit

Answer:

1. How is the `compare_helper_entry` hook point generated?
2. Was absolute VA `0x5028ac` accidentally converted into wrong module offset form?
3. Does current `actual_compare.entry = 0x1028ac` correspond to `0x5028ac - image_base`?
4. Does `mainModule.base.add(offset)` land at the actual compare callee entry?
5. Is the callee in the main module, an import thunk, another module, or a wrapper?
6. Is target process bitness consistent with the current register and stack reader?
7. Is `per-probe-timeout` long enough to observe the compare call after UI trigger?

### B. Callsite argument capture audit

Add or fix hooks so that `module+0x258c` is captured directly.

At minimum inspect:

- `module+0x2584`: `push 5`
- `module+0x2586`: `push 0x551c4c`
- `module+0x258b`: `push esi`
- `module+0x258c`: `call 0x5028ac`
- `module+0x1028ac`: callee entry, only if confirmed as the correct module offset

At `module+0x258c`, read:

- registers: `eax`, `ecx`, `edx`, `esi`, `edi`, `esp`, `ebp`, `eip`
- stack slots: `[esp]`, `[esp+4]`, `[esp+8]`, `[esp+0xc]`, `[esp+0x10]`
- previews for:
  - `esi`
  - `[esp]`
  - `[esp+4]`
  - `[esp+8]`
  - constant pointer `0x551c4c`

Expected callsite stack interpretation:

- Before `call 0x5028ac`, the return address has not yet been pushed.
- Because `push esi` is the last push, `[esp]` should correspond to lhs candidate pointer.
- `[esp+4]` should correspond to `0x551c4c` flag-prefix constant.
- `[esp+8]` should correspond to count `5`, if the push sequence is complete and stack tracking is correct.

Callee-entry interpretation remains separate:

- At callee entry, `[esp]` is return address.
- `[esp+4]` is arg0.
- `[esp+8]` is arg1.
- `[esp+0xc]` may be count.

The artifact must not mix these two layouts.

### C. Required output fields

The new or extended artifact must explicitly report:

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `callee_entry_observed`
- `callee_entry_observed_count`
- `callsite_pre_call_observed`
- `callsite_pre_call_observed_count`
- `callsite_stack_args_observed`
- `lhs_side`
- `flag_side`
- `candidate_dependent_side`
- `constant_flag_prefix_side`
- `arg_layout`
- `module_base`
- `callee_entry_address_audit`
- `breakpoint_probe_allowed`
- `next_bounded_action`

### D. Classification rules

Use these classifications or equivalent explicit names:

1. `compare_callsite_args_identified`
   - callsite pre-call observed for the fixed candidates;
   - one side varies by candidate;
   - one side matches the flag wide-prefix constant;
   - lhs/flag side can be classified.

2. `callee_entry_hook_missed_but_callsite_args_identified`
   - callee entry observed count is zero;
   - callsite pre-call is observed and sufficient to classify args.

3. `compare_hook_coverage_failed`
   - neither callsite nor callee entry is observed;
   - next action must be address/module-base/hook-runtime diagnosis, not Base64/RC4 probing.

4. `inconclusive`
   - some data observed, but not enough to classify lhs/flag side.

`breakpoint_probe_allowed` must remain false unless both of these are true:

- real compare lhs side is confirmed;
- a runtime-backed producer is connected to that compare lhs.

This round is expected to keep Base64/RC4 probing blocked.

## 6. Implementation Scope

Allowed:

- Extend `compare_callsite_reanchor_and_lhs_provenance_audit` with direct callsite argument capture.
- Or add one bounded sidecar, if extension would be messy.
- Add a thin runtime script only if needed.
- Add project_state indexing for the new artifact if a new artifact name is introduced.
- Add negative-cache guidance so failed hook coverage does not trigger candidate expansion or Base64/RC4 probing.
- Add tests for schema, classification, fixed candidates, and project_state indexing.

Not allowed:

- no candidate search expansion
- no new solver/ranker
- no full solve_reports commit
- no broad disassembly scan
- no Base64/RC4 breakpoint probe
- no reuse of old `[ebp-0x1170]` as trusted compare lhs without actual compare-side evidence

Fixed candidate set:

- Use the existing three-candidate set already used by the r5 audit.
- Do not generate new candidates.
- At minimum this should include:
  - `78d540b49c59077041414141414141`
  - `5a3e7f46ddd474d041414141414141`
- Read the third fixed candidate from the existing r5 runner/artifact rather than inventing a new one.

## 7. Tests

Run at minimum:

```bat
python -m py_compile reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py reverse_agent\olly_scripts\compare_callsite_reanchor_and_lhs_provenance_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
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
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_compare_callsite_arg_capture_20260515_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Then rebuild state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_compare_callsite_arg_capture_20260515_r1
python -m reverse_agent.project_state status
```

Required unit coverage:

1. `compare_callsite_args_identified`
   - three candidates observed at callsite;
   - lhs preview varies;
   - flag side preview is constant;
   - classification is correct;
   - `breakpoint_probe_allowed` remains false unless producer connection is also proven.

2. `callee_entry_hook_missed_but_callsite_args_identified`
   - callee observed count is zero;
   - callsite observed count is three;
   - artifact must not remain generic `inconclusive`.

3. `compare_hook_coverage_failed`
   - neither callsite nor callee entry hits;
   - next action points to hook address/module base audit;
   - no search expansion and no Base64/RC4 probe.

4. project_state indexing
   - latest artifact appears in `current_state.json`;
   - bottleneck reason reflects the new classification.

## 8. Stop Conditions

Stop and report if any of the following happens:

1. Compare callsite args are identified.
   - Report exact hook offset.
   - Report lhs side and flag side.
   - Report which side varies across candidates.
   - Keep Base64/RC4 probe blocked unless lhs producer connection is also proven.

2. Callee entry hook is proven wrong but callsite args are identified.
   - Report correct module/VA/RVA interpretation.
   - Preserve callsite result as valid evidence.
   - Do not block progress merely because callee entry hook missed.

3. Hook coverage still fails.
   - Report attach address, module base, target bitness, timeout, and hook error messages.
   - Do not continue to candidate search or Base64/RC4 probe.

4. Implementation requires full `solve_reports` scan or candidate expansion.
   - Stop and explain why this violates current project_state constraints.

5. Tests fail.
   - Stop after collecting failure output.
   - Do not proceed to harness run until unit failures are resolved.

本轮核心判断：下一步不是继续找更多候选，而是把 `module+0x258c` 这个 compare callsite 的参数抓实。只要能在 call 前确认 `esi` 和 `0x551c4c` 两侧关系，后续才有资格继续追 lhs producer；否则 Base64/RC4 探针仍然应该封锁。

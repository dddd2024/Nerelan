# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

当前目标：继续追踪 `ESI` 在 `0x2559..0x258b` 窗口内如何成为最终 compare LHS，也就是明确 `module+0x258b: push esi` 处的 `ESI` 是从哪里来的、是否只是 compare-side handoff/copy，还是已经接近 transform material。

最新状态已经前进：`compare_real_lhs_provenance_audit` 的当前 reason 是 `lhs_register_source_confirmed`，说明 `ESI` 在 `0x258b` 处已经被确认是 compare `arg0` 来源。当前 task 也变为 `Trace ESI source window 0x2559..0x258b`。这轮不应再做“找 ESI 是否等于 arg0”的重复验证，而应进一步缩小 `0x2559..0x258b` 内部的数据来源。

Expected output artifact:

`compare_esi_feeding_window_audit.json`

或窄幅扩展现有：

`compare_real_lhs_provenance_audit.json`

但必须单独输出 `esi_feeding_window` section。

## 2. Current Evidence

当前 active strategy 仍是 `CompareAwareSearchStrategy`。当前 best candidate 没有变化：

- exact2:
  - `78d540b49c59077041414141414141`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`
- exact1/frontier:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wchar count: `1`
  - runtime distance5: `258`

这说明仍然没有证据支持扩大候选搜索。

最新 harness run:

`sr_esi_snapshot_20260515_r4`

最新核心 artifact:

`solve_reports\harness_runs\sr_esi_snapshot_20260515_r4\reports\tool_artifacts\samplereverse\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json`

artifact index 显示该 run 是当前最新 run，`compare_real_lhs_provenance_audit` 是当前最新核心 artifact，且 `missing = []`。

当前 bottleneck:

- stage: `compare_real_lhs_provenance_audit`
- reason: `lhs_register_source_confirmed`
- confidence: `medium`

最新 `compare_real_lhs_provenance_audit` 中已经确认：

- `entry = 0x258c`
- `entry_status = confirmed`
- `lhs_side = arg0`
- `flag_side = arg1`
- `arg0_candidate_dependent = true`
- `arg1_candidate_dependent = false`
- `lhs_preview_varies_by_candidate = true`
- `classification = lhs_register_source_confirmed`
- `pre_compare_lhs_push` at `module+0x258b`:
  - `instruction = push esi`
  - `candidate_dependent = true`
  - `connects_to_compare_lhs = true`
  - `compare_lhs_match_count = 3`
  - `runtime_backed_count = 3`

但仍未确认真正 producer：

- `identified_producers = []`
- `old_slot_ebp_minus_1170_status = rejected`
- `old_slot_ebp_minus_1170_valid = false`
- `breakpoint_probe_allowed = false`
- `next_producer_window = 0x2559..0x258b`
- `next_bounded_action = hook the narrower window feeding ESI before module+0x258b, starting at module+0x2559 and the instruction range immediately before the compare push`

## 3. Do Not Do

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam / budget / timeout / topN.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit full `solve_reports`.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat transform trace consistency audit without new runtime evidence.
8. Do not rerun Base64/RC4 breakpoint probe before real LHS producer identification.
9. Do not reuse old `[ebp-0x1170]` as primary anchor.
10. Do not re-run the previous ESI snapshot unchanged; it already proved `ESI` at `0x258b` connects to compare `arg0`.
11. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic/runtime evidence.
12. Do not scan entire `solve_reports` unless explicitly needed.
13. Do not classify a source as transform material merely because it is candidate-dependent.

Negative cache still blocks:

- old solver blind search;
- budget-only expansion;
- stale `[ebp-0x1170]` reuse;
- Base64/RC4 breakpoint probe before real LHS producer identification.

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

重点代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py`
- `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py`
- `reverse_agent/olly_scripts/*lhs*provenance*.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

只读取 targeted artifacts：

- `solve_reports\harness_runs\sr_esi_snapshot_20260515_r4\reports\tool_artifacts\samplereverse\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json`
- `solve_reports\harness_runs\sr_esi_snapshot_20260515_r4\summary.json`
- `solve_reports\harness_runs\sr_esi_snapshot_20260515_r4\run_manifest.json`
- `solve_reports\harness_runs\sr_esi_snapshot_20260515_r4\reports\tool_artifacts\samplereverse\samplereverse_compare_probe.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_producer_material_confirmation\compare_producer_material_confirmation.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`

Do not load full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports`.

## 5. Required Audit

实现一个 bounded audit：`compare_esi_feeding_window_audit`。

### A. Static window audit: `0x2559..0x258b`

以 `module+0x258b: push esi` 为 sink，精确审计 `0x2559..0x258b` 之间所有可能影响 `ESI` 或 compare arg0 的指令。

必须输出：

- instruction list:
  - rva
  - bytes
  - instruction
  - size
  - boundary status
  - whether writes `ESI`
  - whether reads `[ebp-*]`
  - whether calls helper
  - whether may alter `ESI` by side effect
- control-flow relation:
  - does execution fall through from `0x2559` to `0x258b`
  - any branch into/out of this window
  - any call in this window
  - predecessor basic blocks of `0x258b`
- dataflow hypothesis:
  - `ESI` loaded directly in window
  - `ESI` preserved from earlier block
  - `ESI` altered by helper side effect
  - `ESI` copied from stack/frame slot
  - `ESI` is stale/carry-over from earlier candidate material

### B. Runtime hook points

固定三候选：

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

在以下点做 runtime snapshot：

- `module+0x2559`
- every instruction boundary between `0x2559` and `0x258b`
- `module+0x2584`
- `module+0x2586`
- `module+0x258b`
- `module+0x258c`

如果 window 内存在 call，则额外 hook：

- call before
- callee enter if in module and hookable
- return site
- call after

每个 hook 采集：

- candidate hex
- hit count
- module offset
- instruction
- EIP / ESP / EBP
- before/after registers if possible:
  - `eax`
  - `ecx`
  - `edx`
  - `esi`
  - `edi`
- previews:
  - `esi_preview`
  - `eax_preview`
  - `edx_preview`
  - confirmed compare arg0 preview
- stack words:
  - `[esp]`
  - `[esp+4]`
  - `[esp+8]`
  - `[esp+0xc]`
  - `[esp+0x10]`
- diagnostic frame slots:
  - `[ebp-0x1168]`
  - `[ebp-0x116c]`
  - `[ebp-0x1170]`
- whether `ESI == confirmed compare arg0`
- whether `ESI preview == confirmed compare arg0 preview`
- whether value or preview varies by candidate

### C. Confirmed compare arg0 reference

Use latest `compare_real_lhs_provenance_audit` as source of truth.

For each candidate, import:

- `actual_compare.arg0_value_by_candidate`
- `actual_compare.arg0_preview_by_candidate`
- `actual_compare.arg1_value_by_candidate`
- `actual_compare.arg1_preview_by_candidate`
- `lhs_side = arg0`
- `flag_side = arg1`

The audit must compare all ESI/window observations against confirmed compare `arg0`, not against `[ebp-0x1170]`.

### D. Required classification

Top-level classification must be one of:

1. `esi_feeding_instruction_identified`
   - a specific instruction in `0x2559..0x258b` writes or establishes `ESI`;
   - runtime-backed;
   - connects to compare `arg0` across fixed candidates.

2. `esi_preserved_from_earlier_block`
   - `ESI` already equals confirmed compare `arg0` at first hook in this window;
   - no instruction in `0x2559..0x258b` creates it;
   - next action must move earlier in CFG.

3. `esi_helper_side_effect_suspected`
   - a call in or immediately before the window changes or establishes `ESI`;
   - needs a narrower helper return/entry audit.

4. `esi_window_rejected`
   - bounded window does not explain ESI source;
   - next action moves to predecessor block, not search expansion.

5. `esi_window_hook_coverage_failed`
   - hooks did not hit or were unreadable due to address/boundary/path/timeout/UI issue.

6. `inconclusive`
   - partial evidence exists but not enough to classify.

Top-level fields:

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `esi_sink`
- `window_start`
- `window_end`
- `confirmed_compare_arg0_by_candidate`
- `confirmed_compare_arg0_preview_by_candidate`
- `window_instruction_table`
- `runtime_snapshots_by_offset`
- `esi_value_by_offset_and_candidate`
- `esi_matches_arg0_by_offset`
- `esi_transition_points`
- `helper_side_effect_candidates`
- `predecessor_blocks`
- `old_frame_anchor_status`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` must stay false unless this audit proves both:

- real LHS producer is runtime-backed;
- producer is transform material, not merely compare-side handoff/copy.

本轮预期大概率仍然不允许 Base64/RC4 probe。

## 6. Implementation Scope

Allowed:

- Add one bounded sidecar: `compare_esi_feeding_window_audit`.
- Or narrowly extend `compare_real_lhs_provenance_audit` with an `esi_feeding_window` section.
- Add one thin runtime script if needed.
- Add project_state indexing for new artifact if new artifact name is used.
- Add tests for:
  - static window table
  - ESI match across candidates
  - preserved-from-earlier classification
  - helper-side-effect classification
  - project_state indexing
- Update `codex_execution_report.md` to reflect the latest 2026-05-15 run and this new result.

Not allowed:

- no candidate generation
- no search expansion
- no Base64/RC4 breakpoint probe
- no full solve_reports scan
- no reuse of `[ebp-0x1170]` as primary source
- no classification based only on candidate dependence
- no assumption that `0x401b50` is transform material without new evidence

## 7. Tests

Minimum compile checks:

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

If new runtime script is added:

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

Runtime validation:

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_esi_feeding_window_20260515_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Rebuild state:

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_esi_feeding_window_20260515_r1
python -m reverse_agent.project_state status
```

Required test coverage:

1. `esi_feeding_instruction_identified`
   - runtime-backed instruction establishes ESI;
   - ESI matches compare arg0 across three candidates.

2. `esi_preserved_from_earlier_block`
   - ESI already matches compare arg0 at window entry;
   - no write in window;
   - next action points earlier in CFG.

3. `esi_helper_side_effect_suspected`
   - call/return relation changes ESI or related pointer;
   - next action narrows to helper.

4. `esi_window_rejected`
   - window cannot explain source;
   - no search expansion triggered.

5. `esi_window_hook_coverage_failed`
   - hooks fail for path/address/boundary/runtime reason;
   - no semantic rejection inferred.

6. project_state indexing
   - new artifact appears in current_state;
   - bottleneck reason reflects classification.

## 8. Stop Conditions

Stop and report if:

1. A specific ESI-feeding instruction is identified.
   - Report offset, instruction, before/after ESI, and three-candidate match.
   - State whether it is copy/handoff or potential transform material.
   - Keep Base64/RC4 blocked unless transform material is proven.

2. ESI is preserved from an earlier block.
   - Report first hook where ESI already equals arg0.
   - Provide next predecessor block/window to inspect.

3. Helper side effect is suspected.
   - Report call offset, return site, ESI before/after.
   - Propose a bounded helper enter/return audit.

4. Current window is rejected.
   - Report why.
   - Move earlier in CFG, not into candidate search.

5. Hook coverage fails.
   - Report address, module base, boundary, timeout, UI/runtime errors.

6. Tests fail.
   - Stop after collecting failure output.
   - Do not run harness until fixed.

本轮核心判断：`0x258b: push esi` 已经证明 `ESI` 是 compare LHS。现在要回答的是：`0x2559..0x258b` 这段窗口内到底是谁让 `ESI` 变成该 LHS；如果窗口入口处 ESI 已经是 LHS，就继续往更早 predecessor block 追，而不是回到候选搜索或 Base64/RC4 probe。

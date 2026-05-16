# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

本轮目标：调查 `compare_lhs_slot_writer_source_audit` 为什么卡在 `writer_hook_not_reached`，并修正 writer/source 路径的 hook 选择。

最新状态已经推进到：

- stage: `compare_lhs_slot_writer_source_audit`
- reason: `writer_hook_not_reached`
- task: `Investigate stalled compare lhs slot writer/source path`

因此下一步不是重复追 `[ebp-0x1170]` 的旧计划，而是处理一个更具体的问题：

`0x253a: mov dword ptr [ebp-0x1170], eax` 被静态识别为 slot writer，但 runtime hook 没有命中。需要判断是 hook 地址 / module base / patched sample 路径错了，还是实际执行路径绕过了 `0x253a`。

Expected output artifact:

`compare_lhs_slot_writer_hook_coverage_audit.json`

或者如果更适合复用现有框架，也可以扩展：

`compare_lhs_slot_writer_source_audit.json`

但必须明确标记本轮是在处理：

`writer_hook_not_reached`

## 2. Current Evidence

当前 active strategy 仍是：

`CompareAwareSearchStrategy`

当前 best candidate 未变：

- exact2:
  - `78d540b49c59077041414141414141`
  - runtime exact wchar count: `2`
  - runtime distance5: `246`
- exact1/frontier:
  - `5a3e7f46ddd474d041414141414141`
  - runtime exact wchar count: `1`
  - runtime distance5: `258`

说明目前没有理由扩展候选搜索。

最新 harness run：

`sr_lhs_slot_writer_source_20260516_r2`

核心 artifact：

`solve_reports\harness_runs\sr_lhs_slot_writer_source_20260516_r2\reports\tool_artifacts\samplereverse_patched\compare_lhs_slot_writer_source_audit\compare_lhs_slot_writer_source_audit.json`

artifact index 显示该 artifact 已成为最新核心结果，且 `missing = []`。

当前关键结果：

- `classification = writer_hook_not_reached`
- `breakpoint_probe_allowed = false`
- `runtime_backed_count = 3`
- actual compare entry 已确认：
  - `actual_compare.entry_status = confirmed`
  - `actual_compare.observed_count = 3`
  - `lhs_side = arg0`
  - `flag_side = arg1`
  - `arg0_candidate_dependent = true`
  - `arg1_candidate_dependent = false`
- slot writer 未命中：
  - hook name: `slot_writer`
  - module offset: `0x253a`
  - instruction: `mov dword ptr [ebp - 0x1170], eax`
  - observed_count: `0`
  - runtime_backed_count: `0`
- 但上游 context hook 命中：
  - hook name: `upstream_candidate_context`
  - module offset: `0x2312`
  - instruction: `sub eax, dword ptr [edx - 4]`
  - observed_count: `3`
  - candidate-dependent fields include `[ebp-0x1168]`, `[ebp-0x1170]`, `edi`, `edx`

重要判断：`0x258c` compare 参数已经能抓到，说明 compare entry / arg capture 已经可用。问题集中在 slot writer hook 没有命中，不是 compare 入口不可达。

`project_state/codex_execution_report.md` 仍停留在 2026-05-14 / 2026-05-13 旧记录，没有同步最新 `sr_lhs_slot_writer_source_20260516_r2`。Codex 本轮结束必须补写最新 CODEX_EXECUTION_REPORT。

## 3. Do Not Do

1. Do not return to old `sample_solver` blind search.
2. Do not only increase beam / budget / timeout / topN.
3. Do not use `compare_semantics_agree=false` candidates as primary frontier.
4. Do not commit full `solve_reports`.
5. Do not repeat exact2 basin value-pool evaluation.
6. Do not repeat H1/H3 fixed 8-candidate Base64 boundary contrast set.
7. Do not repeat current 5-candidate transform trace consistency audit without new runtime evidence.
8. Do not rerun Base64/RC4 breakpoint probe before confirming a real material construction hook.
9. Do not repeat compare return-site audit.
10. Do not repeat producer material confirmation without instruction-level evidence.
11. Do not rerun old `0x2559` material hook after slot writer/source audit.
12. Do not run Base64/RC4 breakpoint probe before slot writer/source validation.
13. Do not treat `0x4019e0`, `0x401b50`, `0x4018cd`, or `0x401be3` as Base64/RC4 material producers without new semantic evidence.
14. Do not treat `0x2312` as material producer unless it is connected to compare arg0 by runtime-backed evidence.
15. Do not treat static existence of `0x253a` as runtime writer proof.
16. Do not scan entire `solve_reports` unless explicitly needed.

Negative cache already blocks old blind search, budget-only expansion, old `0x2559` material-hook repetition, and Base64/RC4 probe before slot writer/source validation.

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

重点代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/project_state.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/olly_scripts/*slot*writer*.py`
- `reverse_agent/olly_scripts/*writer*source*.py`
- `reverse_agent/olly_scripts/*provenance*.py`
- `reverse_agent/olly_scripts/*compare*.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

Targeted artifacts only：

- `solve_reports\harness_runs\sr_lhs_slot_writer_source_20260516_r2\summary.json`
- `solve_reports\harness_runs\sr_lhs_slot_writer_source_20260516_r2\run_manifest.json`
- `solve_reports\harness_runs\sr_lhs_slot_writer_source_20260516_r2\reports\tool_artifacts\samplereverse_patched\compare_lhs_slot_writer_source_audit\compare_lhs_slot_writer_source_audit.json`
- `solve_reports\harness_runs\sr_lhs_slot_writer_source_20260516_r2\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.json`
- `solve_reports\tool_artifacts\samplereverse_base64_rc4_static_point_discovery_20260508\base64_rc4_static_point_discovery.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`

Do not load full `PROJECT_PROGRESS_LOG.txt` or full `solve_reports`.

## 5. Required Audit

实现一个 bounded debug pass：

`compare_lhs_slot_writer_hook_coverage_audit`

目标不是重新证明 compare LHS，而是解释：

为什么 actual compare 已命中 3 次，但 `0x253a` slot writer hook 没命中？

### A. Hook coverage audit

必须检查：

1. `0x253a` 是否真在当前 `samplereverse_patched` binary / current module 中。
2. `samplereverse` 与 `samplereverse_patched` 的 module offset 是否有偏移差异。
3. runtime script 是否把 `0x253a` 绑定到了错误 module base。
4. `0x253a` 是否因为 instruction boundary / delayed attach / breakpoint timing 导致 miss。
5. `0x253a` 是否不是当前执行路径上的 writer，只是静态窗口里的候选 writer。
6. 是否存在另一个实际 writer，直接导致 compare arg0 变成 candidate-dependent buffer。

### B. Compare-backed backtrace

由于 actual compare 已确认：

- compare call at `0x258c`
- lhs = arg0
- flag = arg1
- arg0 varies by candidate

下一步应从 `actual_compare.arg0_value_by_candidate` 反推来源：

1. 在 compare entry 处记录 arg0 pointer。
2. 向前追最近一次写入该 pointer 的 frame slot / register。
3. 对比 `[ebp-0x1170]`、`[ebp-0x1168]`、`[ebp-0x116c]` 是否等于 compare arg0。
4. 若 `[ebp-0x1170]` 不等于 compare arg0，则旧 slot 假设要降级。
5. 若 `[ebp-0x1170]` 等于 compare arg0，但 `0x253a` 未命中，则优先修 hook coverage，而不是换方向。

### C. Use existing runtime evidence

必须复用当前 `compare_lhs_slot_writer_source_audit` 的发现：

- `0x2312` 命中 3 次；
- `[ebp-0x1168]`、`edx` 呈现候选相关；
- actual compare arg0 呈现候选相关；
- slot writer `0x253a` 未命中。

不要重新做大范围搜索。只允许围绕：

`0x2312 -> 0x253a -> 0x258c`

增加小窗口 hook。

### D. Required classification

新 artifact 顶层 classification 必须是以下之一：

1. `HOOK_ADDRESS_FIXED`
   - 证明原 `0x253a` hook 地址或 module base 错；
   - 已修正并命中 writer。

2. `STATIC_WRITER_NOT_ON_RUNTIME_PATH`
   - 证明 `0x253a` 不是当前 runtime path 的 writer；
   - 需要转向实际 writer。

3. `SLOT_WRITER_CONFIRMED`
   - 修复 hook 后 `0x253a` 命中；
   - `[ebp-0x1170]` 与 compare arg0 建立 runtime-backed relation。

4. `ARG0_SOURCE_IDENTIFIED`
   - 不依赖 `0x253a`，直接从 compare arg0 反推出实际 source。

5. `UPSTREAM_CONTEXT_ONLY`
   - 只能确认 `0x2312` candidate-dependent context，但无法连接到 compare arg0。

6. `HOOK_COVERAGE_FAILED`

7. `INCONCLUSIVE`

### E. Required fields

artifact 必须包含：

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `actual_compare`
- `slot_writer_probe`
- `hook_address_audit`
- `module_base_check`
- `patched_binary_check`
- `arg0_backtrace`
- `slot_to_arg0_relation`
- `upstream_context_relation`
- `identified_actual_writer`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` 仍必须保持 `false`，除非实际 writer/source 已被 runtime-backed 证明为 transform material。

## 6. Implementation Scope

Allowed：

- 增加或修正 `compare_lhs_slot_writer_source_audit`。
- 或新增一个薄层 audit：
  - `compare_lhs_slot_writer_hook_coverage_audit`
- 只加小窗口 runtime hooks：
  - `0x2312`
  - `0x253a`
  - `0x2554`
  - `0x2559`
  - `0x258b`
  - `0x258c`
- 增加 module base / patched binary offset 检查。
- 增加 project_state indexing。
- 更新 negative cache，避免再次重复未命中的 `0x253a` hook。
- 更新 `codex_execution_report.md`，补上 2026-05-16 最新执行结果。

Not allowed：

- 不生成新候选。
- 不扩 beam/budget。
- 不跑 Base64/RC4 breakpoint probe。
- 不提交 runtime artifact 目录。
- 不把 `0x2312` 直接当 material producer，除非能连接到 compare arg0。
- 不把 `0x253a` 静态存在当作 runtime writer 证据。

## 7. Tests

Compile checks：

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

如果新增或修改 runtime script：

```bat
python -m py_compile reverse_agent\olly_scripts\compare_lhs_slot_writer_source_audit.py
python -m py_compile reverse_agent\olly_scripts\<new_script>.py
```

Targeted tests：

```bat
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

Full tests：

```bat
python -m pytest -q
```

Runtime validation：

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_slot_writer_coverage_20260516_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

Rebuild state：

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_slot_writer_coverage_20260516_r1
python -m reverse_agent.project_state status
```

Required test coverage：

1. writer hook not reached -> classified as hook coverage issue, not semantic rejection.
2. corrected hook address -> `HOOK_ADDRESS_FIXED`.
3. static writer not on runtime path -> `STATIC_WRITER_NOT_ON_RUNTIME_PATH`.
4. actual compare arg0 source identified -> `ARG0_SOURCE_IDENTIFIED`.
5. Base64/RC4 gate remains blocked.
6. project_state indexes latest audit.

## 8. Stop Conditions

Stop and report if：

1. `0x253a` hook 地址问题被确认。
   - 报告正确 offset / module base。
   - 报告是否已经命中 writer。

2. `0x253a` 被证明不在 runtime path。
   - 报告实际 writer/source。
   - 下一步转向 actual writer。

3. compare arg0 source 被识别。
   - 报告 source slot/register。
   - 报告是否 candidate-dependent。
   - 报告是否连接 transform material。

4. 只能确认 `0x2312` 上游 context。
   - 报告为什么不能连到 compare arg0。
   - 下一步继续小窗口追踪，不扩大搜索。

5. hook coverage 仍失败。
   - 报告具体失败原因：module base、patched binary、bad boundary、timing、UI/runtime error。

6. 测试失败。
   - 停止并给出失败输出。
   - 不运行 harness。

本轮一句话：不要重复追 `[ebp-0x1170]` 的旧计划；现在要专门解释为什么 `0x253a` writer hook 没命中，并从已确认的 `0x258c arg0` 反向定位真实 writer/source。

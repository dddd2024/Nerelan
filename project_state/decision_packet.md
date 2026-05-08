# DECISION_PACKET

## 1. Goal

利用已发现的 compare-producer hook evidence，把瓶颈从：

```text
base64_rc4_static_point_discovery / hookable_points_found
```

推进到：

```text
定位 base64_input / base64_output / rc4_key / rc4_input / rc4_output 的实际生产路径或可 hook 指令点
```

上一轮 Codex 已确认：

- `base64_rc4_static_point_discovery` 产出成功；
- 找到了 3 个 instruction-confirmed compare-producer hook 点；
- 但没有找到 instruction-confirmed Base64/RC4 material construction point；
- 因此 `base64_rc4_breakpoint_probe` 仍然不允许直接重跑。

下一步不是扩大候选搜索，而是围绕 `module+0x2559` 和 `module+0x1b50` 做 bounded trace / backward slice。

## 2. Current Evidence

当前 active strategy 是 `CompareAwareSearchStrategy`，目标样本是 `samplereverse`，主线仍是 `L15(prefix8)`。已知 transform 链路是：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

当前 best candidate 仍然是：

```text
exact2:
78d540b49c59077041414141414141
runtime_ci_exact_wchars=2
runtime_ci_distance5=246
compare_semantics_agree=true

frontier/exact1:
5a3e7f46ddd474d041414141414141
runtime_ci_exact_wchars=1
runtime_ci_distance5=258
compare_semantics_agree=true
```

当前瓶颈已经不是“没有 hook 点”，而是“只找到了 compare-producer hook 点，没有找到 Base64/RC4 材料点”。`current_state.json` 里 `latest_base64_rc4_static_point_discovery` 显示：

```text
classification = hookable_points_found
hookable_count = 3
instruction_confirmed_count = 3
breakpoint_probe_allowed = false
```

三个高可信 hook 点是：

```text
post_handoff_lhs_reload  module+0x2559
handoff_helper_enter     module+0x1b50
handoff_helper_return    module+0x2559
```

但 Base64、RC4 KSA、RC4 PRGA、encrypted_const、UTF-16LE 都仍然是 `found_but_not_hookable`。

`artifact_index.json` 也显示一些下一阶段 probe 还没有产物，例如：

```text
compare_handoff_probe = null
compare_handoff_return_site_probe = null
compare_handoff_slice_probe = null
compare_producer_trace_probe = null
pre_rc4_material_probe = null
```

这说明下一步应优先填补这些 compact probe artifact，而不是重复已有的大型搜索。

## 3. Do Not Do

Codex 下一轮不要做这些事：

```text
1. 不要回到 old sample_solver blind search。
2. 不要只扩大 beam、budget、topN、timeout 或 frontier iteration。
3. 不要把 compare_semantics_agree=false 的候选作为主突破点。
4. 不要提交完整 solve_reports。
5. 不要重复 exact2 basin value-pool evaluation。
6. 不要重复 H1/H3 fixed 8-candidate Base64 boundary contrast set。
7. 不要在没有新 runtime evidence 的情况下重复 transform trace consistency audit。
8. 不要直接重跑 base64_rc4_breakpoint_probe。
9. 不要再次只做 base64_rc4_static_point_discovery，本轮应使用它的结果继续推进。
```

这些方向已经在 `negative_results.json` 里明确标为 do-not-repeat，其中 `compare_semantics_agree=false` 作为主 frontier 是 hard block，完整提交 `solve_reports` 也是 hard block。

## 4. Files To Inspect

Codex 先检查这些文件：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md

reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py

tests/test_compare_aware_search_strategy.py
tests/test_tool_runners.py
tests/test_project_state.py
```

如果已有以下 probe 文件或同名逻辑，优先复用，不要重复实现：

```text
compare_handoff_probe
compare_handoff_return_site_probe
compare_handoff_slice_probe
compare_producer_trace_probe
dynamic_compare_path_probe
pre_rc4_material_probe
```

只读取必要 artifact，不扫描完整 `solve_reports`。

## 5. Required Audit

Codex 在改代码前必须先审计：

```text
1. module+0x2559 和 module+0x1b50 分别处于什么指令上下文。
2. 0x2559 的 lhs reload / handoff return 是否读取 compare buffer 指针、长度、栈槽或寄存器。
3. 0x1b50 的 handoff helper enter 是否能看到调用者传入的 buffer、key、encoded data 或中间态。
4. compare buffer 的上游写入点来自：
   - Base64 output?
   - RC4 output?
   - UTF-16LE payload?
   - encrypted const decrypt result?
   - 还是额外 wrapper/handoff copy?
5. 当前自动静态发现为什么只能确认 compare_producer，不能确认 Base64/RC4。
6. 是否需要从 compare-producer 向前做 bounded backward slice，而不是继续找 Base64 字母表或 RC4 KSA signature。
```

## 6. Implementation Scope

### A. 新增或补全 bounded compare-producer trace probe

目标不是求解 flag，而是拿到中间材料证据。

建议 artifact 名称：

```text
compare_producer_trace_probe
```

输出 compact JSON，例如：

```json
{
  "classification": "compare_producer_trace_captured | compare_only_capture | upstream_material_candidate_found | manual_disassembly_required | runtime_execution_failure",
  "hook_points": [
    {
      "name": "handoff_helper_enter",
      "module_offset": "0x1b50",
      "captured_registers": {},
      "captured_stack_slots": {},
      "candidate_buffers": []
    },
    {
      "name": "post_handoff_lhs_reload",
      "module_offset": "0x2559",
      "captured_registers": {},
      "captured_stack_slots": {},
      "candidate_buffers": []
    }
  ],
  "candidate_materials": [
    {
      "kind": "compare_buffer | possible_base64_output | possible_rc4_output | possible_utf16le_payload | unknown_buffer",
      "address": "0x...",
      "size": 0,
      "preview_hex": "...",
      "preview_ascii": "...",
      "evidence": []
    }
  ],
  "next_bounded_action": "..."
}
```

### B. 从 compare-producer 向前做 bounded slice

Codex 应围绕 `module+0x2559` 和 `module+0x1b50` 做小范围静态/动态结合分析：

```text
1. 记录进入 0x1b50 时的参数寄存器和关键栈槽。
2. 记录返回到 0x2559 前后的寄存器、栈槽、内存指针。
3. 对 compare buffer 地址做 watch/write-source 分析。
4. 追踪最近一次写入 compare buffer 的指令。
5. 若写入来源是另一个 buffer copy，则继续限定深度向前追 1-2 层。
```

最大深度要固定，不能演变成全程序动态搜索。

### C. 只在 material hook 被确认后，才允许重跑 breakpoint probe

本轮可以允许的升级条件：

```text
breakpoint_probe_ready =
  至少发现一个 instruction-confirmed 且 hookable=true 的 material point，
  kind 属于 base64_output / rc4_input / rc4_output / rc4_key / utf16le_payload。
```

否则仍然禁止重跑 `base64_rc4_breakpoint_probe`。

### D. 更新 project_state

新增或更新 compact 字段：

```text
latest_compare_producer_trace_probe
latest_compare_handoff_slice_probe
latest_pre_rc4_material_probe
```

不要写入大型 runtime dump。只保留：

```text
artifact path
classification
hook point count
candidate material count
best material candidates
next_bounded_action
```

## 7. Tests

最低测试命令：

```powershell
python -m py_compile reverse_agent\olly_scripts\base64_rc4_breakpoint_probe.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_tool_runners.py tests/test_project_state.py
python -m pytest -q
```

如果新增 probe runner，需要补充测试：

```text
1. compare_producer_trace_probe artifact schema。
2. project_state compact rendering。
3. breakpoint_probe_allowed 仍然 false，除非 material point instruction-confirmed。
4. 不改变 candidate ranking。
5. 不扩大 beam/budget/topN/timeout。
6. 不提交 full solve_reports。
```

上轮全量测试是 `187 passed`，所以本轮改动后必须至少保持这个基线不退化。

## 8. Stop Conditions

Codex 遇到以下任一情况就停止并写报告：

```text
1. 0x2559 / 0x1b50 只能捕获 compare_buffer，无法看到上游材料。
2. compare buffer 的上游写入点无法在 bounded depth 内定位。
3. 发现疑似 Base64/RC4 material，但没有 instruction-level evidence。
4. 需要人工 IDA/x64dbg 确认具体指令。
5. 自动 trace 会变成全程序搜索。
6. 需要扩大 candidate search 才能继续。
7. 候选排名意外变化。
8. 出现 exact3+ 或 distance5 优于 246。
```

Codex 报告里的最终分类必须是以下之一：

```text
compare_producer_trace_captured
compare_only_capture
upstream_material_candidate_found
breakpoint_probe_ready
base64_material_captured
rc4_material_captured
manual_disassembly_required
runtime_execution_failure
```

## Expected Codex Output

Codex 下一轮应产出：

```text
project_state/codex_execution_report.md
updated project_state/current_state.json
updated project_state/artifact_index.json
updated/added tests
optional compact artifact:
  compare_producer_trace_probe.json
  compare_handoff_slice_probe.json
  pre_rc4_material_probe.json
```

一句话总结：**下一轮不要继续“找候选”，也不要重复 static discovery；要从已确认的 compare-producer 指令 `0x2559 / 0x1b50` 反向追踪 compare buffer 的生产路径，争取找到 Base64/RC4 中间材料的可断点位置。**

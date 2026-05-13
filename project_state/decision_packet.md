# DECISION_PACKET

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

本轮目标：

**围绕 `post_handoff_branch_outcome_audit` 的 `post_handoff_window_rejected` 结果，定位 compare lhs 的真实 producer / branch outcome。**

不要继续把 `0x233d / 0x2346` 当作 material-hook 主方向，也不要提前探测 `0x234e / 0x2355`。当前证据已经表明这些方向在现阶段被阻塞，下一步应先解释：

```text
compare lhs 是从哪个 branch / call outcome 进入 [ebp-0x1170] 或 compare 参数的？
```

核心目标不是扩大候选搜索，而是把 compare-only 捕获向上游回溯一层，找出真正连接 transform chain 的生产点。

## 2. Current Evidence

当前 active strategy：

```text
CompareAwareSearchStrategy
```

当前任务：

```text
Investigate stalled post_handoff_branch_outcome_audit path
```

当前瓶颈：

```text
stage: post_handoff_branch_outcome_audit
reason: post_handoff_window_rejected
confidence: medium
```

当前最佳候选仍然是：

```text
78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true
```

frontier 候选是：

```text
5a3e7f46ddd474d041414141414141
runtime_ci_exact_wchars = 1
runtime_ci_distance5 = 258
compare_semantics_agree = true
```

已知变换链：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

但目前 Base64/RC4 probe 仍是 compare-only：

```text
compare_buffer = available
utf16le_payload = unavailable
base64_input = unavailable
base64_output = unavailable
rc4_input = unavailable
rc4_key = unavailable
rc4_output = unavailable
```

`0x233d / 0x2346` 曾被标记为 candidate-dependent、hookable、instruction-confirmed，但后续 negative cache 已经明确：不要在 post-handoff audit 已拒绝之后继续复用它们作为 material-hook breakpoints。

Codex 上轮已经实现了 `material_hook_runtime_validation` gate，并加了 timeout guard，测试通过；但这个方向现在不应继续原样重复。

## 3. Do Not Do

本轮 Codex 禁止做：

```text
不要回到 old sample_solver blind search
不要只扩大 beam / budget / guided pool
不要使用 compare_semantics_agree=false 候选作为主 frontier
不要提交完整 solve_reports
不要重复 exact2 basin value-pool
不要重复 H1/H3 fixed contrast set
不要重复 transform trace consistency audit
不要重复旧 Base64/RC4 breakpoint probe
不要重复 focused dynamic compare-path probe
不要重复 memory-scan lower-level pre-RC4/key material probe
不要继续沿用旧 0x401b50 -> 0x2559 helper 假设
不要复用 0x233d/0x2346 作为 material-hook breakpoints
不要在 branch outcome 未到达前 probe downstream 0x234e/0x2355
不要扫描完整 PROJECT_PROGRESS_LOG.txt
不要扫描完整 solve_reports
```

这些方向已经进入 negative cache，其中部分是 hard block。

## 4. Files To Inspect

优先检查：

```text
reverse_agent/function_semantics.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须读取的 project_state：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

只在必要时读取这些 artifact，不要展开完整 `solve_reports`：

```text
solve_reports\harness_runs\sr_post_handoff_audit_20260512_r4\reports\tool_artifacts\samplereverse_patched\post_handoff_branch_outcome_audit\post_handoff_branch_outcome_audit.json

solve_reports\harness_runs\sr_post_handoff_audit_20260512_r4\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_pre_compare_handoff_target_probe\compare_pre_compare_handoff_target_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_producer_trace_probe\compare_producer_trace_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_producer_material_confirmation\compare_producer_material_confirmation.json
```

## 5. Required Audit

### A. 审计 `post_handoff_branch_outcome_audit` 的 rejected 原因

Codex 需要先明确回答：

```text
post_handoff_window_rejected 具体拒绝了哪个窗口？
哪些 hook 点 hit？
哪些 hook 点 missed？
哪些寄存器 / 栈槽 / compare 参数关系不成立？
```

重点整理以下关系：

```text
[ebp-0x1170] 是否仍是 compare lhs slot
0x253a 是否稳定写入 candidate output pointer
0x2554 call 0x401b50 后是否真的影响 compare lhs
0x2559 reload 的值是否与 compare arg0 / arg1 对齐
0x258b push esi 前 esi 是否可解释为 compare lhs
0x258c compare call 参数是否能稳定捕获
```

不要只复述 artifact，要形成一个小的 relation table。

### B. 重新建立 compare lhs producer 候选表

本轮要产出一个新的 compact artifact，建议命名：

```text
compare_lhs_producer_audit.json
```

建议字段：

```json
{
  "classification": "producer_identified | producer_window_rejected | inconclusive",
  "candidate_count": 3,
  "checked_windows": [
    {
      "name": "pre_lhs_slot_store",
      "rva": "0x253a",
      "hit": true,
      "candidate_dependent": true,
      "connects_to_compare_lhs": true
    }
  ],
  "relations": {
    "slot_to_compare_arg": "confirmed | rejected | inconclusive",
    "eax_to_slot": "confirmed | rejected | inconclusive",
    "esi_to_compare_arg": "confirmed | rejected | inconclusive",
    "helper_return_to_lhs": "confirmed | rejected | inconclusive"
  },
  "next_bounded_action": "..."
}
```

### C. 对 3 个候选做最小 cross-candidate 差分

至少使用：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
一个单字节扰动候选，例如修改第 8 或第 9 字节
```

需要记录：

```text
0x253a 前后 EAX / [ebp-0x1170]
0x2559 后 ESI / [ebp-0x1170]
0x258b push esi 前 ESI
0x258c compare call arg0 / arg1 preview
compare lhs preview
```

目标是确认哪个字段真正随候选变化，并且能流入 compare。

### D. 如果 producer 明确，才允许下一步走 material hook

只有当 Codex 能证明某个 producer window 同时满足：

```text
candidate_dependent = true
connects_to_compare_lhs = true
instruction_confirmed = true
runtime_backed_count >= 3
```

才允许下一轮以该 producer 为基础继续寻找 UTF-16LE/Base64/RC4 material。

否则不允许继续 Base64/RC4 probe。

## 6. Implementation Scope

本轮实现范围要小：

```text
1. 新增或修正一个 bounded audit step：compare_lhs_producer_audit
2. 只围绕 compare lhs producer / slot / compare args 做审计
3. 不改候选搜索主逻辑
4. 不扩大 beam / budget
5. 不引入新的大规模 candidate generation
6. 不提交完整 solve_reports
7. 更新 project_state/current_state.json
8. 更新 project_state/artifact_index.json
9. 更新 project_state/task_packet.json
10. 如果发现明确失败方向，追加 negative_results.json
```

如果已有类似 audit step，不要重复造轮子，优先复用并补 relation classification。

## 7. Tests

至少运行：

```powershell
python -m py_compile reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
```

```powershell
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
```

如果新增 artifact schema 或 strategy step，再运行：

```powershell
python -m pytest -q
```

最后重建 project_state：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_run_name>
```

上轮全量测试基线是：

```text
204 passed
```

## 8. Stop Conditions

### 成功停止

满足任一条件就停止并生成 `CODEX_EXECUTION_REPORT`：

```text
确认 compare lhs 的真实 producer window
确认某个 instruction-confirmed hook 点 candidate-dependent 且 connects_to_compare_lhs
确认新的 upstream window 可作为下一轮 UTF-16LE/Base64/RC4 material hook 起点
```

### 有效失败停止

满足任一条件也停止：

```text
确认 0x253a / 0x2559 / 0x258b / 0x258c 这一组窗口无法解释真实 compare lhs 来源
确认当前 post-handoff window 只能得到 compare-only，无法连接 transform chain
确认需要回到更早的 branch/call outcome，但当前 artifact 不足以定位
```

此时必须写入 negative cache，并给出下一个最小 bounded action。

### 禁止继续条件

```text
没有新增 runtime evidence，不允许扩大搜索
没有确认 producer，不允许 Base64/RC4 breakpoint probe
没有确认 branch outcome 到达，不允许 probe 0x234e / 0x2355
不能重复 0x233d / 0x2346 material hook
不能扫描完整 solve_reports
```

这轮的核心判断：**先把 compare lhs 的真实来源钉死，再谈 Base64/RC4。现在继续猜候选或继续探旧 material hook，收益很低。**

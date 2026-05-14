# DECISION_PACKET

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

本轮目标：

**实现一个 bounded `compare_callsite_reanchor_and_lhs_provenance_audit`，从真实 compare 调用和 lhs 参数出发，重新锚定 compare callsite、caller frame、lhs pointer 来源。**

当前不要再假设：

```text
[ebp-0x1170] / 0x253a / 0x2554 / 0x2559 / 0x258b
```

这一组窗口就是真实 compare lhs producer。上一轮 `compare_lhs_producer_audit` 已经把该窗口分类为：

```text
classification = producer_window_rejected
next_bounded_action = move earlier than 0x253a..0x258b
```

本轮的核心问题是：

```text
真实 compare helper 被调用时：
1. 调用点到底是不是 module+0x258c？
2. compare lhs 是 arg0 还是 arg1？
3. lhs 指针来自哪个 caller/frame/stack slot/register？
4. lhs buffer 最近一次候选相关写入来自哪个上游 instruction/call？
```

目标不是搜索新候选，而是修正动态证据链的锚点。

## 2. Current Evidence

当前策略：

```text
CompareAwareSearchStrategy
```

当前样本：

```text
samplereverse
```

当前主线：

```text
L15(prefix8)
```

当前最佳候选仍然是：

```text
78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true
```

当前瓶颈：

```text
stage = compare_lhs_producer_audit
reason = producer_window_rejected
confidence = medium
```

最新 artifact 已经确认：

```text
compare_lhs_producer_audit.runtime_backed_count = 3
compare_lhs_producer_audit.classification = producer_window_rejected
breakpoint_probe_allowed = false
identified_producers = []
```

上一轮 checked windows 结果：

```text
0x253a pre_lhs_slot_store:
  runtime_backed = 3
  candidate_dependent = false
  connects_to_compare_lhs = false

0x2554 pre_handoff_call:
  runtime_backed = 1
  candidate_dependent = false
  connects_to_compare_lhs = false

0x2559 post_handoff_lhs_reload:
  runtime_backed = 0
  hookable = false

0x258b pre_compare_lhs_push:
  runtime_backed = 0
  hookable = false

0x1028ac compare_helper_entry:
  runtime_backed = 0
  hookable = false
```

现有 relation 均未闭合：

```text
eax_to_slot = inconclusive
slot_to_compare_arg = inconclusive
esi_to_compare_arg = inconclusive
helper_return_to_lhs = inconclusive
```

已知变换链仍是：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

但 Base64/RC4 breakpoint 仍未被授权，因为没有 instruction-confirmed、candidate-dependent、connects_to_compare_lhs 的 material hook。最新 artifact 索引显示 `compare_lhs_producer_audit` 是最新有效产物，而 `base64_rc4_breakpoint_probe`、`compare_producer_trace_probe`、`compare_pre_compare_handoff_target_probe` 等仍为空或不可作为当前直接突破点。

## 3. Do Not Do

本轮 Codex 禁止做：

```text
不要回到 old sample_solver blind search
不要扩大 beam / budget / topN / timeout
不要用 compare_semantics_agree=false 候选作为主 frontier
不要提交完整 solve_reports
不要重复 exact2 basin value-pool evaluation
不要重复 H1/H3 fixed contrast set
不要重复 transform trace consistency audit
不要直接 rerun Base64/RC4 breakpoint probe
不要重复 compare return-site audit
不要重复 producer material confirmation，除非新增 instruction-level evidence
不要把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 直接当作 Base64/RC4 producer
不要扫描完整 PROJECT_PROGRESS_LOG.txt
不要扫描完整 solve_reports
```

这些方向已写入 negative cache，尤其是：

```text
run Base64/RC4 breakpoint probe directly from compare lhs producer audit
```

已经被明确禁止；该 audit 只提供下一步 bounded material-hook start，不授权 Base64/RC4 probe。

## 4. Files To Inspect

必须先读：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

代码侧优先检查：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/function_semantics.py
reverse_agent/project_state.py
reverse_agent/olly_scripts/compare_lhs_producer_audit.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

只按需读取 indexed artifacts，不要展开完整 `solve_reports`：

```text
solve_reports\harness_runs\sr_lhs_prod_20260513_r1\reports\tool_artifacts\samplereverse_patched\compare_lhs_producer_audit\compare_lhs_producer_audit.json

solve_reports\harness_runs\sr_lhs_prod_20260513_r1\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.json

solve_reports\harness_runs\sr_lhs_prod_20260513_r1\case_results\samplereverse-compare-producer-backtrace.json
```

如果这些 runtime artifacts 未被提交到仓库，则在本地读取；不要让 GPT 端猜测其内容。

## 5. Required Audit

### A. Compare callsite re-anchor

Codex 必须先回答：

```text
实际 compare helper 的入口地址是什么？
实际 compare call 的 caller return address 是什么？
实际 caller module offset 是否等于 0x258c 附近？
compare arg0 / arg1 哪一侧是 flag target？
compare arg0 / arg1 哪一侧是 candidate-dependent lhs？
```

输出一个 relation table：

```text
field                         status
actual_compare_entry           confirmed / rejected / inconclusive
actual_compare_caller_rva      ...
arg0_candidate_dependent       true / false / unknown
arg1_candidate_dependent       true / false / unknown
flag_side                      arg0 / arg1 / unknown
lhs_side                       arg0 / arg1 / unknown
lhs_preview_varies_by_candidate true / false
```

### B. Frame re-anchor

上一轮 `[ebp-0x1170]` 方向被 rejected 后，本轮必须确认：

```text
当前 hook 读到的 EBP 是否属于真实 compare caller frame？
[ebp-0x1170] 是否确实是本次 compare 的 lhs slot？
如果不是，真实 lhs pointer 来自哪个 register / stack slot？
```

不要继续沿用旧 frame 假设。

### C. LHS pointer provenance

以真实 compare lhs pointer 为起点，做 bounded provenance：

```text
1. 捕获 compare 入口 arg0/arg1 pointer 和 preview
2. 找出 candidate-dependent 的 lhs pointer
3. 在同一进程/同一 invocation 中，向上游追踪 lhs buffer 最近一次写入
4. 优先限定到当前函数或 caller 前后小窗口，不做全局内存扫描
```

建议 artifact 名称：

```text
compare_callsite_reanchor_and_lhs_provenance_audit.json
```

建议 schema：

```json
{
  "classification": "lhs_producer_identified | callsite_reanchored_but_producer_unknown | frame_anchor_rejected | inconclusive",
  "candidate_count": 3,
  "runtime_backed_count": 0,
  "actual_compare": {
    "entry": "",
    "caller_return_address": "",
    "caller_module_offset": "",
    "arg0_preview_by_candidate": {},
    "arg1_preview_by_candidate": {},
    "lhs_side": "arg0 | arg1 | unknown",
    "flag_side": "arg0 | arg1 | unknown"
  },
  "frame_anchor": {
    "old_slot_ebp_minus_1170_valid": false,
    "actual_lhs_source": "register | stack_slot | heap_ptr | unknown",
    "actual_lhs_source_detail": ""
  },
  "provenance": {
    "candidate_dependent": false,
    "connects_to_compare_lhs": false,
    "producer_instruction": "",
    "producer_call": "",
    "evidence": []
  },
  "breakpoint_probe_allowed": false,
  "next_bounded_action": ""
}
```

### D. Candidate set

使用固定 3 个候选即可：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

不要生成新候选集；第三个只作为单点扰动对照。

### E. Gate for next step

只有满足以下条件，下一轮才允许进入 material hook / Base64 / RC4 方向：

```text
actual compare callsite confirmed
lhs side confirmed
lhs preview candidate-dependent
producer instruction/call connects_to_compare_lhs
runtime_backed_count >= 3
```

否则继续阻断 Base64/RC4 breakpoint probe。

## 6. Implementation Scope

本轮允许的修改范围：

```text
1. 新增一个 bounded audit step：
   compare_callsite_reanchor_and_lhs_provenance_audit

2. 复用已有 compare probe / Frida / UIA collector 形状

3. 只增加 compact artifact，不提交完整 solve_reports

4. 更新 project_state indexing：
   latest_compare_callsite_reanchor_and_lhs_provenance_audit

5. 更新 current_state / task_packet 的 current_bottleneck

6. 必要时追加 negative_results：
   old frame anchor rejected
   0x253a..0x258b rejected as lhs producer
```

不允许改：

```text
candidate ranking
frontier strategy
beam / budget / timeout
sample_solver blind search
offline transform model
```

## 7. Tests

至少运行：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_lhs_producer_audit.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
```

如果新增脚本，例如：

```text
reverse_agent\olly_scripts\compare_callsite_reanchor_and_lhs_provenance_audit.py
```

则加入：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_callsite_reanchor_and_lhs_provenance_audit.py
```

再运行：

```powershell
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

如果新增 artifact schema / project_state index：

```powershell
python -m pytest -q
```

最后本地重建状态：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_run_name>
python -m reverse_agent.project_state status
```

上轮测试基线：

```text
212 passed
```

## 8. Stop Conditions

### 成功停止

满足任一条件即停止：

```text
确认真实 compare callsite 和 lhs side
确认旧 [ebp-0x1170] frame anchor 是错误假设
确认真实 lhs producer instruction/call
确认一个 candidate-dependent 且 connects_to_compare_lhs 的上游 hook
```

此时生成 `CODEX_EXECUTION_REPORT`，并把下一步收敛到该 producer 的 material hook。

### 有效失败停止

满足任一条件也停止：

```text
实际 compare callsite 无法稳定捕获
lhs side 无法区分
lhs preview 不随候选变化
旧 0x253a..0x258b 窗口被再次证明确实不是 producer
artifact 不足以继续 provenance
```

此时必须写入 negative cache，并给出下一个 bounded action。

### 禁止继续条件

```text
没有确认 actual compare callsite，不允许继续上游 material probe
没有确认 lhs side，不允许 Base64/RC4 breakpoint probe
没有 candidate-dependent lhs preview，不允许扩大搜索
没有 connects_to_compare_lhs，不允许把任何 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 标为 material producer
```

本轮核心判断：

**先从真实 compare 调用重新锚定 lhs 指针，再追 producer。旧的 post-handoff 窗口已经被 rejected，继续沿旧窗口或扩大搜索都不是有效下一步。**

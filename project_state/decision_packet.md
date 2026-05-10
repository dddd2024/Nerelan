# DECISION_PACKET

## 1. Goal

本轮目标不是继续扩大搜索，而是做一个**最小控制流/数据流确认任务**：

```text
确认 0x2338 -> 0x401b50 调用之后，为什么 0x233d / 0x234e / 0x2355 没有被当前探针观测到。
```

核心要解决的问题：

```text
0x401b50 是否只是 handoff/copy/helper？
还是它确实参与 UTF-16LE / Base64 / RC4 材料链？
```

只有当新的证据证明某个点满足：

```text
instruction_confirmed = true
hookable = true
candidate_dependent = true
connected_to_compare_lhs_or_transform_chain = true
```

才允许打开 Base64/RC4 breakpoint probe。

当前 `project_state` 已经把瓶颈定位为：

```text
stage = function_semantic_audit
reason = runtime_instrumentation_required
```

上一轮 Codex 已经实现 Function Semantic Audit Layer，并且完整测试通过。

## 2. Current Evidence

当前主线：

```text
sample/profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_mainline = L15(prefix8)
known_transform = input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

当前最好候选仍然是 exact2：

```text
candidate_hex = 78d540b49c59077041414141414141
runtime_ci_exact_wchars = 2
runtime_ci_distance5 = 246
compare_semantics_agree = true
source = pairscan
```

当前 frontier 候选：

```text
candidate_hex = 5a3e7f46ddd474d041414141414141
runtime_ci_exact_wchars = 1
runtime_ci_distance5 = 258
```

上一轮语义审计结果：

```text
classification = runtime_instrumentation_required
function_count = 4
material_hook_candidate_count = 0
breakpoint_probe_allowed = false
```

四个函数当前状态：

```text
0x4019e0: instruction-confirmed, but not candidate-dependent
0x401b50: strongest bounded suspect; 0x2338 reached for 3 diagnostic candidates
0x4018cd: downstream call site, current probe not reached
0x401be3: downstream call site, current probe not reached
```

Codex 报告明确指出下一步是：

```text
Add the smallest runtime/static confirmation for the 0x2338 -> 0x401b50 call outcome:
determine why 0x233d, 0x234e, and 0x2355 are not reached.
```

## 3. Do Not Do

不要做以下事情：

```text
1. 不要回到 old sample_solver blind search。
2. 不要只增加 beam / budget / timeout / topN。
3. 不要把 compare_semantics_agree=false 的候选作为主 frontier。
4. 不要提交完整 solve_reports。
5. 不要重复 exact2 basin value-pool evaluation。
6. 不要重复 H1/H3 fixed Base64 boundary contrast set。
7. 不要在没有新运行时证据的情况下重复 transform trace consistency audit。
8. 不要在没有确认 Base64/RC4/UTF-16LE instruction hook 前运行 Base64/RC4 breakpoint probe。
9. 不要把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 material producer，除非有新的 candidate-dependent 语义证据。
10. 不要扫描完整 solve_reports。
```

这些限制已经写入 `negative_results.json`，其中 `compare_semantics_agree=false` 和提交完整 `solve_reports` 是硬性阻断方向。

## 4. Files To Inspect

Codex 必须先读：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
```

然后检查实现位置：

```text
reverse_agent/function_semantics.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

重点搜索这些关键词：

```text
function_semantic_audit
breakpoint_probe_allowed
candidate_dependent
material_hook_candidate
compare_producer_material_confirmation
producer_pre_material_call
0x2338
0x233d
0x234e
0x2355
0x401b50
```

如果存在 Olly/x32dbg/运行时探针脚本，再检查：

```text
reverse_agent/olly_scripts/*compare*
reverse_agent/olly_scripts/*material*
reverse_agent/olly_scripts/*semantic*
reverse_agent/olly_scripts/*probe*
```

## 5. Required Audit

### A. Static control-flow audit

围绕以下窗口做精确审计：

```text
0x2312
0x2320
0x2325
0x2338
0x233d
0x2346
0x234e
0x2353
0x2355
0x235a
```

必须回答：

```text
1. 0x2338 call 0x401b50 是否正常返回？
2. 如果没有到达 0x233d，是因为：
   - 0x401b50 内部直接跳转？
   - 异常 / early exit？
   - hook 点设置错误？
   - 地址基址/RVA 映射错误？
   - 当前候选走了另一条路径？
3. 0x401b50 返回后 EAX / EDX / ECX / ESI 的值如何变化？
4. [ebp-0x1168] / [ebp-0x116c] / [ebp-0x1170] 是否被写入？
5. 哪个值最终进入 compare lhs？
```

### B. Runtime micro-probe audit

新增或修改一个**最小运行时探针**，只围绕：

```text
entry: 0x2338
return/next: 0x233d
downstream: 0x234e, 0x2355
callee: 0x401b50
```

不允许做大范围追踪。

探针至少记录：

```json
{
  "candidate_hex": "...",
  "hit_0x2338": true,
  "hit_0x233d": false,
  "hit_0x234e": false,
  "hit_0x2355": false,
  "call_0x401b50_entered": true,
  "call_0x401b50_returned": false,
  "return_address": "...",
  "eax_before": "...",
  "eax_after": "...",
  "edx_before": "...",
  "edx_after": "...",
  "esi_before": "...",
  "esi_after": "...",
  "stack_slots": {
    "ebp_minus_1168": "...",
    "ebp_minus_116c": "...",
    "ebp_minus_1170": "..."
  },
  "candidate_dependent_fields": [],
  "classification": "..."
}
```

### C. Candidate-dependence audit

至少用 3 个候选做对照：

```text
1. current exact2:
   78d540b49c59077041414141414141

2. current frontier:
   5a3e7f46ddd474d041414141414141

3. one controlled neighbor:
   78d540b49c59077141414141414141
```

目标不是找更优 candidate，而是判断：

```text
0x401b50 前后是否出现 candidate-dependent 差异。
```

如果所有寄存器、栈槽、返回路径都不随 candidate 改变，则必须把 `0x401b50` 降级为：

```text
copy_or_handoff
allocator_or_container_helper
string_helper
unknown_but_bounded
```

不要继续把它当 Base64/RC4 producer。

### D. Hook-readiness audit

不得把 `breakpoint_probe_allowed` 设为 true，除非同时满足：

```text
1. semantic_guess 属于：
   - utf16le_constructor
   - base64_transform
   - rc4_ksa
   - rc4_prga
   - rc4_transform

2. instruction_confirmed = true
3. hookable = true
4. candidate_dependent = true
5. output connected to compare lhs or known transform chain
```

否则继续保持：

```text
breakpoint_probe_allowed = false
```

并写明缺失证据。

## 6. Implementation Scope

### Phase 1: Add minimal call-outcome probe

添加一个小型、可复用的 probe，不要写成 samplereverse 专用硬编码。

建议命名：

```text
compare_handoff_return_site_probe
producer_call_outcome_probe
material_call_outcome_probe
```

产物路径建议：

```text
solve_reports/.../tool_artifacts/<sample>/compare_handoff_return_site_probe/compare_handoff_return_site_probe.json
```

### Phase 2: Integrate result into Function Semantic Audit

把新证据回填到：

```text
function_semantics["0x401b50"]
```

至少更新：

```text
candidate_dependent
hookable
instruction_confirmed
material_hook_candidate_status
semantic_guess
confidence
positive_evidence
negative_evidence
next_required_evidence
```

### Phase 3: Update project_state summary

`current_state.json` 应该新增或更新：

```json
{
  "latest_compare_handoff_return_site_probe": {
    "artifact": "...",
    "classification": "...",
    "candidate_count": 3,
    "hit_0x2338_count": 3,
    "hit_0x233d_count": 0,
    "candidate_dependent_count": 0,
    "next_bounded_action": "..."
  }
}
```

如果确认 `0x401b50` 非 material producer，要把 `function_semantics["0x401b50"]` 的状态降级。

如果确认它有 candidate-dependent output，则标记为下一轮可进入 material hook confirmation，但仍不直接跑 Base64/RC4 probe，除非 hook-readiness 全部满足。

### Phase 4: Update negative_results

如果本轮证明 `0x401b50` 不产生 candidate-dependent material，则写入新的 soft block：

```json
{
  "direction": "treat 0x401b50 as material producer after 0x2338 without new candidate-dependent return evidence",
  "scope": "function_semantics",
  "function": "0x401b50",
  "do_not_repeat": true,
  "severity": "soft_block",
  "reason": "0x2338 call outcome probe showed no candidate-dependent output / no return-site connection",
  "evidence_artifact": "..."
}
```

### Phase 5: Preserve candidate search behavior

不得修改：

```text
candidate generation
candidate ranking
frontier promotion
beam
budget
timeout
topN
solver scoring
```

本轮是证据层任务，不是搜索策略任务。

## 7. Tests

最低测试：

```bash
python -m py_compile reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
```

如果新增 probe 脚本：

```bash
python -m py_compile reverse_agent\olly_scripts\<new_probe>.py
```

如果改了 artifact indexing / project_state：

```bash
python -m pytest -q
```

上一轮基线是：

```text
196 passed
```

本轮不得引入回归。

## 8. Stop Conditions

Codex 遇到以下任一情况就停止并报告：

```text
1. 证明 0x401b50 正常返回到 0x233d。
2. 证明 0x401b50 不返回到 0x233d，并解释原因。
3. 证明 0x401b50 前后存在 candidate-dependent output。
4. 证明 0x401b50 前后不存在 candidate-dependent output。
5. 证明 0x233d / 0x234e / 0x2355 未命中是 hook/address/path 问题。
6. 找到新的 instruction-confirmed + hookable + candidate-dependent material hook。
7. 需要人工 IDA/x32dbg 检查才能继续。
8. 任何 exact3+ 或 distance5 改进出现。
9. candidate ranking 意外变化。
10. 测试失败且无法在本轮修复。
```

最终 `CODEX_EXECUTION_REPORT` 必须包含：

```text
1. 本轮新增/修改了什么 probe。
2. 0x2338 是否命中。
3. 0x401b50 是否进入。
4. 0x401b50 是否返回。
5. 0x233d / 0x234e / 0x2355 为什么没有命中。
6. 是否发现 candidate-dependent register/stack/memory field。
7. 0x401b50 当前语义分类是什么。
8. breakpoint_probe_allowed 是否仍为 false。
9. 是否有候选改善。
10. 哪些测试通过。
```

一句话给 Codex：

```text
Do the smallest runtime/static confirmation of the 0x2338 -> 0x401b50 call outcome, explain why 0x233d/0x234e/0x2355 are not reached, update function_semantics and project_state with candidate-dependence evidence, and keep Base64/RC4 breakpoint probing gated unless a material hook becomes instruction-confirmed, hookable, candidate-dependent, and connected to the compare lhs or transform chain.
```

# DECISION_PACKET

## 1. Goal

围绕 `samplereverse` 当前瓶颈继续推进：

**验证 `0x233d` 和 `0x2346` 这两个已确认、可 hook、candidate-dependent 的 material hook 点，捕获它们附近的真实运行时材料，并判断它们是否能把 compare-only 捕获推进到 UTF-16LE / Base64 / RC4 链路材料。**

当前事实源显示 active strategy 是 `CompareAwareSearchStrategy`，当前任务是 `Investigate stalled function_semantic_audit path`，瓶颈阶段是 `function_semantic_audit`，状态为 `material_hook_ready`。

## 2. Current Evidence

当前最佳候选仍然没有变：

- exact2：`78d540b49c59077041414141414141`
  - `runtime_ci_exact_wchars = 2`
  - `runtime_ci_distance5 = 246`
- frontier / exact1：`5a3e7f46ddd474d041414141414141`
  - `runtime_ci_exact_wchars = 1`
  - `runtime_ci_distance5 = 258`

这些候选都要求 `compare_semantics_agree = true`，不能把语义不一致的候选作为主 frontier。

已知变换链是：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

当前最关键的新证据是：

- `0x233d`
  - `semantic_guess = utf16le_constructor`
  - `candidate_dependent = true`
  - `instruction_confirmed = true`
  - `hookable = true`
  - `material_hook_candidate_status = ready`
- `0x2346`
  - 同样是 `utf16le_constructor`
  - 同样 ready

而 `0x401b50` 被归类为 `copy_or_handoff`，状态是 `blocked_copy_handoff_only`，不应继续按旧假设把它当作核心 Base64/RC4 producer。

最近一次 Base64/RC4 breakpoint probe 的分类是 `base64_rc4_compare_only`：只捕获到了 `compare_buffer`，`base64_input / base64_output / rc4_input / rc4_key / rc4_output / utf16le_payload` 都是 unavailable。下一步应该审计 hook placement，而不是重复原 probe。

artifact index 显示最新运行目录是：

```text
solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512
```

最新相关 artifacts 包括：

```text
function_semantic_audit
compare_pre_compare_handoff_target_probe
base64_rc4_breakpoint_probe
base64_rc4_static_point_discovery
compare_producer_material_confirmation
compare_producer_trace_probe
```

这些足够支撑下一轮，不需要默认读取完整 `solve_reports`。

## 3. Do Not Do

Codex 本轮禁止做这些事：

1. 不要回到旧的 `sample_solver` blind search。
2. 不要只扩大 beam、budget 或 guided pool。
3. 不要把 `compare_semantics_agree=false` 的候选作为主 frontier。
4. 不要提交完整 `solve_reports`。
5. 不要重复 exact2 basin value-pool 分支。
6. 不要重复 H1/H3 fixed 8-candidate prefix8 contrast set。
7. 不要重复当前 5-candidate transform trace consistency audit，除非有新的 runtime evidence。
8. 不要在没有确认新的 Base64/RC4 instruction hook 前重复旧 Base64/RC4 breakpoint probe。
9. 不要继续沿用旧的 `0x401b50 -> 0x2559` helper 假设。
10. 不要默认扫描完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports`。

这些方向已经在 negative cache 中被标记为 soft/hard block。

## 4. Files To Inspect

优先检查：

```text
reverse_agent/function_semantics.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必要时只读取以下 artifact，不要展开完整 solve_reports：

```text
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\function_semantic_audit\function_semantic_audit.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\compare_pre_compare_handoff_target_probe\compare_pre_compare_handoff_target_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\base64_rc4_breakpoint_probe\base64_rc4_breakpoint_probe.json

solve_reports\harness_runs\samplereverse_pre_compare_handoff_target_20260512\reports\tool_artifacts\samplereverse_patched\base64_rc4_static_point_discovery\base64_rc4_static_point_discovery.json
```

## 5. Required Audit

Codex 需要做一个小范围、证据驱动的 runtime/static audit。

### A. 对 `0x233d` 和 `0x2346` 做 hook 点确认

确认这两个点在当前 active candidate 下：

```text
0x233d: mov edx, dword ptr [ebp - 0x116c]
0x2346: push edx
```

需要记录：

```text
EAX / EDX / ECX / ESI / EDI
[ebp-0x116c]
[ebp-0x1168]
[ebp-0x1170]
stack top around push edx
candidate preview bytes
wide-char interpretation if possible
```

目标不是直接解 flag，而是确认这些数据是否是：

```text
raw input
UTF-16LE input
Base64 input
Base64 output
RC4 input
RC4 output
compare lhs
```

### B. 对 3 个代表候选做 cross-candidate 差分

至少使用：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
一个边界扰动候选，例如只改第 8 字节或第 9 字节
```

记录每个候选在 `0x233d / 0x2346` 附近捕获到的 buffer preview，并判断哪些字段是 candidate-dependent。

### C. 建立 material-kind 分类

新增或更新 artifact，输出类似：

```json
{
  "classification": "utf16le_material_captured | base64_boundary_candidate | compare_only | inconclusive",
  "hook_points": ["0x233d", "0x2346"],
  "candidate_count": 3,
  "captured_material": {
    "utf16le_payload": "available/unavailable",
    "base64_input": "available/unavailable",
    "base64_output": "available/unavailable",
    "rc4_input": "available/unavailable",
    "rc4_output": "available/unavailable",
    "compare_buffer": "available/unavailable"
  },
  "next_bounded_action": "..."
}
```

### D. 只在有新证据时解锁 Base64/RC4 probe

如果 `0x233d / 0x2346` 捕获到的材料能稳定连接到 UTF-16LE 或后续 transform chain，再允许下一步构造新的 Base64/RC4 breakpoint probe。

如果仍然只到 compare buffer，保持 `base64_rc4_breakpoint_probe_allowed = false`。

## 6. Implementation Scope

本轮实现范围应保持很小：

1. 在 `CompareAwareSearchStrategy` 里增加一个 bounded probe 或 audit step，名称建议：

```text
pre_compare_material_hook_probe
```

2. 只围绕 `0x233d / 0x2346` 采集材料。
3. 输出 compact artifact，不提交完整运行目录。
4. 更新 `project_state/current_state.json`、`artifact_index.json`、`task_packet.json`。
5. 如发现明确 negative result，追加到 `negative_results.json`，避免下一轮重复。

不要改候选搜索主逻辑，除非 audit 明确证明某个 captured material 可直接形成新的 prefix constraint。

## 7. Tests

至少运行：

```powershell
python -m py_compile reverse_agent\function_semantics.py reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
```

```powershell
python -m pytest -q tests/test_compare_aware_search_strategy.py tests/test_project_state.py
```

如果改动 probe 或 artifact schema，再运行：

```powershell
python -m pytest -q
```

最后重新构建 project_state：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_run_name>
```

此前 Codex 的完整测试基线是 `196 passed`，可以作为回归参考。

## 8. Stop Conditions

Codex 在以下任一条件满足时停止，并生成新的 `CODEX_EXECUTION_REPORT`。

### 成功停止

捕获到以下任一类新材料：

```text
utf16le_payload available
base64_input available
base64_output available
rc4_input available
rc4_output available
```

并且能说明它与候选输入或 compare lhs 的关系。

### 有效失败停止

确认：

```text
0x233d / 0x2346 虽然 hookable 且 candidate-dependent，
但只能解释为 copy/handoff 或无法连接到 transform chain
```

此时必须把该方向写入 negative cache，并给出下一个最小 bounded action。

### 禁止继续条件

如果只得到 compare buffer，不能继续重复 Base64/RC4 breakpoint probe。

如果没有新增 runtime evidence，不能扩大搜索预算。

如果需要完整 `PROJECT_PROGRESS_LOG.txt` 才能判断，先停止并说明 project_state 信息不足。

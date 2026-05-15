# DECISION_PACKET.md

Generated for `samplereverse` from the latest `project_state` facts.

## 1. Goal

当前目标：从已经确认的 compare LHS 侧 `arg0` 反向追踪真实 producer，证明 `arg0` 的候选相关 buffer 是由哪个 instruction / call / frame slot 产生，并判断它是否连接到 UTF-16LE/Base64/RC4 transform chain。

上一轮目标已经完成：最新状态显示 compare callsite 已经 re-anchor 成功，`actual_compare.entry_status = confirmed`，`observed_count = 3`，`lhs_side = arg0`，`flag_side = arg1`，`arg0_candidate_dependent = true`，`arg1_candidate_dependent = false`。当前 bottleneck 已经变成 `callsite_reanchored_but_producer_unknown`。

本轮不要再修 callsite 参数捕获。下一步应新增或扩展一个 bounded provenance trace：

`compare_lhs_arg0_provenance_trace.json`

核心问题：

> 已确认的 compare `arg0` 指针分别为 `0x480cdd0`、`0x41bcdd0`、`0x3cccdd0` 等候选相关 buffer。这个 buffer 是从哪个 producer 写入/返回/拷贝出来的？它是否来自 `0x2312..0x2338` 附近的 upstream material，还是来自更靠近 compare callsite 的其他路径？

## 2. Current Evidence

当前 active strategy 是 `CompareAwareSearchStrategy`。当前 best 仍然是 exact2 candidate `78d540b49c59077041414141414141`，runtime exact wchar count 为 2，distance5 为 246；frontier / exact1 candidate 仍是 `5a3e7f46ddd474d041414141414141`。

最新 harness run 是：

`sr_cmpcap_20260515_r4`

最新核心 artifact 是：

`solve_reports\harness_runs\sr_cmpcap_20260515_r4\reports\tool_artifacts\samplereverse_patched\compare_callsite_reanchor_and_lhs_provenance_audit\compare_callsite_reanchor_and_lhs_provenance_audit.json`

已确认 compare callsite：

- `actual_compare.entry = 0x258c`
- `caller_module_offset = 0x258c`
- `entry_status = confirmed`
- `observed_count = 3`
- `lhs_side = arg0`
- `flag_side = arg1`
- `arg0_candidate_dependent = true`
- `arg1_candidate_dependent = false`
- `lhs_preview_varies_by_candidate = true`
- `classification = callsite_reanchored_but_producer_unknown`
- `breakpoint_probe_allowed = false`

已确认参数关系：

- `arg0` 是候选相关 LHS buffer。
- `arg1` 是常量 flag side，preview 为 UTF-16LE 风格的 `flag{...}` 固定字符串。
- `arg0_value_by_candidate` 随候选变化：
  - `78d540b49c59077041414141414141` -> `0x480cdd0`
  - `78d540b49c59076f41414141414141` -> `0x41bcdd0`
  - `5a3e7f46ddd474d041414141414141` -> `0x3cccdd0`

但 producer 仍未确认：

- `identified_producers = []`
- `provenance.connects_to_compare_lhs = false`
- `provenance.candidate_dependent = false`
- old `[ebp-0x1170]` 仍然不能作为可信 anchor。
- `next_bounded_action = narrow provenance from the confirmed lhs side before any material probe`

已有负面约束仍然生效：不能直接从 callsite re-anchor audit 进入 Base64/RC4 breakpoint probe，因为还缺少 runtime-backed lhs producer connected to compare lhs。

## 3. Do Not Do

1. 不要回到旧 `sample_solver` blind search。
2. 不要只增加 beam、budget、timeout、topN 或候选池。
3. 不要使用 `compare_semantics_agree=false` 候选作为主 frontier。
4. 不要提交完整 `solve_reports`。
5. 不要重复 exact2 basin value-pool evaluation。
6. 不要重复 H1/H3 fixed 8-candidate Base64 boundary contrast set。
7. 不要重复 transform trace consistency audit，除非有新 runtime evidence。
8. 不要再重复“修 callsite 参数捕获”的任务；它已经确认成功。
9. 不要复用旧 `[ebp-0x1170]` frame anchor，除非能证明它实际连接到 compare `arg0`。
10. 不要直接运行 Base64/RC4 breakpoint probe。
11. 不要把 `0x4019e0`、`0x401b50`、`0x4018cd`、`0x401be3` 当成 Base64/RC4 material producer，除非新增语义/runtime 证据。
12. 不要扫描完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports`。
13. 不要把 `arg0` 的候选相关性误解为“已经找到 producer”；现在只证明了 compare LHS 侧，不等于证明来源。

## 4. Files To Inspect

先读 project state：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`

注意：`codex_execution_report.md` 目前仍停留在 2026-05-14 的旧报告，其中还记录 r5 为 `inconclusive`；但最新 `current_state.json` 和 `artifact_index.json` 已经指向 2026-05-15 的 `sr_cmpcap_20260515_r4`，状态比报告更新。Codex 本轮结束时必须补写最新 CODEX_EXECUTION_REPORT。

再检查代码：

- `reverse_agent/strategies/compare_aware_search.py`
- `reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py`
- `reverse_agent/olly_scripts/compare_callsite_reanchor_and_lhs_provenance_audit.py`
- `reverse_agent/function_semantics.py`
- `reverse_agent/project_state.py`
- `tests/test_compare_aware_search_strategy.py`
- `tests/test_project_state.py`

只读取以下 targeted artifacts：

- `solve_reports\harness_runs\sr_cmpcap_20260515_r4\reports\tool_artifacts\samplereverse_patched\compare_callsite_reanchor_and_lhs_provenance_audit\compare_callsite_reanchor_and_lhs_provenance_audit.json`
- `solve_reports\harness_runs\sr_cmpcap_20260515_r4\summary.json`
- `solve_reports\harness_runs\sr_cmpcap_20260515_r4\run_manifest.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_producer_material_confirmation\compare_producer_material_confirmation.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\compare_handoff_return_site_probe\compare_handoff_return_site_probe.json`
- `solve_reports\tool_artifacts\samplereverse_handoff_return_outcome_manual_20260510\function_semantic_audit\function_semantic_audit.json`

## 5. Required Audit

实现或扩展一个 bounded audit：`compare_lhs_arg0_provenance_trace`。

### A. 从 confirmed compare arg0 反向追踪

以每个候选的 compare `arg0_value` 为目标指针：

- `0x480cdd0`
- `0x41bcdd0`
- `0x3cccdd0`

在 runtime 中围绕以下 hook 点观察这些指针何时出现、从哪里被复制、何时进入 `esi`、何时进入 stack arg0：

- `module+0x2312`
- `module+0x2320`
- `module+0x2325`
- `module+0x2338`
- `module+0x233d`
- `module+0x2346`
- `module+0x253a`
- `module+0x2554`
- `module+0x2559`
- `module+0x2584`
- `module+0x2586`
- `module+0x258b`
- `module+0x258c`

### B. 必须区分三类关系

对每个 hook 点，判断：

1. Pointer identity match
   - register / stack slot / frame slot 的值是否等于 confirmed compare `arg0` 指针。

2. Preview/content match
   - hook 点处的 buffer preview 是否与 compare `arg0_preview` 相同或具有稳定前缀关系。

3. Candidate dependence
   - 同一 hook 点的值或 preview 是否随三候选变化。

不能只看 candidate-dependent；必须证明它连接到 compare `arg0`。

### C. 采集字段

每个候选、每个 hook 点至少采集：

- hit count
- module offset
- instruction
- register values:
  - `eax`
  - `ecx`
  - `edx`
  - `esi`
  - `edi`
  - `esp`
  - `ebp`
- register previews:
  - `eax_preview`
  - `ecx_preview`
  - `edx_preview`
  - `esi_preview`
  - `edi_preview`
- stack words:
  - `[esp]`
  - `[esp+4]`
  - `[esp+8]`
  - `[esp+0xc]`
  - `[esp+0x10]`
- frame slots:
  - `[ebp-0x1168]`
  - `[ebp-0x116c]`
  - `[ebp-0x1170]`
- compare arg0 target pointer for this candidate
- whether each observed value equals compare arg0 pointer
- whether preview matches compare arg0 preview
- whether hook appears before or after callsite `0x258c`

### D. Classification

Artifact 顶层 classification 必须是以下之一：

1. `lhs_producer_identified`
   - 找到 runtime-backed hook；
   - 该 hook 的 register/slot pointer 或 output preview 连接到 confirmed compare `arg0`；
   - 三候选上关系成立。

2. `lhs_producer_candidate_dependent_but_unconnected`
   - 找到候选相关 material；
   - 但 pointer/preview 不能连接到 confirmed compare `arg0`。

3. `lhs_producer_window_rejected`
   - 当前 `0x2312..0x258c` bounded window 内没有 producer 连接到 compare `arg0`。

4. `lhs_producer_hook_coverage_failed`
   - 关键 hook 未命中或无法读，不得据此推断语义。

5. `inconclusive`
   - 有部分证据，但不足以判断 producer。

Artifact 顶层字段：

- `classification`
- `candidate_count`
- `runtime_backed_count`
- `confirmed_lhs_side`
- `confirmed_flag_side`
- `compare_arg0_by_candidate`
- `compare_arg0_preview_by_candidate`
- `producer_candidates`
- `producer_connected_points`
- `candidate_dependent_unconnected_points`
- `rejected_points`
- `hook_coverage_failures`
- `breakpoint_probe_allowed`
- `next_bounded_action`

`breakpoint_probe_allowed` 仍然必须默认为 false。只有当 producer 已识别并且能证明其是 transform material，才允许下一轮考虑 Base64/RC4 probe。

## 6. Implementation Scope

允许：

- 新增一个 bounded sidecar：`compare_lhs_arg0_provenance_trace`。
- 或窄幅扩展 `compare_callsite_reanchor_and_lhs_provenance_audit`，但不要让该 artifact 变得语义混乱。
- 新增一个薄 runtime script。
- 在 strategy 中只加入固定三候选调度。
- project_state 增加 latest artifact indexing。
- negative_results 增加 producer trace 相关 blocks。
- 更新 `codex_execution_report.md` 到最新 2026-05-15 状态。

不允许：

- 不允许生成新候选。
- 不允许搜索扩展。
- 不允许直接运行 Base64/RC4 breakpoint probe。
- 不允许扫描全量 `solve_reports`。
- 不允许把旧 `[ebp-0x1170]` 当成事实来源。
- 不允许仅凭 `candidate_dependent=true` 就分类为 producer。

固定候选集：

- `78d540b49c59077041414141414141`
- `78d540b49c59076f41414141414141`
- `5a3e7f46ddd474d041414141414141`

这些候选来自最新 compare callsite audit 的三候选观测，不要临时替换。

## 7. Tests

至少运行：

```bat
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\function_semantics.py
```

如果新增 runtime script：

```bat
python -m py_compile reverse_agent\olly_scripts\<new_script>.py
```

定向测试：

```bat
python -m pytest -q tests\test_compare_aware_search_strategy.py tests\test_project_state.py
```

全量测试：

```bat
python -m pytest -q
```

真实 harness：

```bat
python -m reverse_agent.harness --dataset solve_reports\samplereverse_compare_producer_backtrace_20260508_dataset.json --run-name sr_lhs_arg0_provenance_20260515_r1 --reports-dir solve_reports --analysis-mode Auto --model-type "Copilot CLI" --runtime-validation-enabled --tool-enabled
```

重建状态：

```bat
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_arg0_provenance_20260515_r1
python -m reverse_agent.project_state status
```

测试必须覆盖：

1. `lhs_producer_identified`
   - 三候选都观测到 producer；
   - producer pointer 或 preview 连接到 compare `arg0`；
   - `breakpoint_probe_allowed` 仍需受 transform material gate 控制。

2. `lhs_producer_candidate_dependent_but_unconnected`
   - hook 点 candidate-dependent；
   - 但不匹配 compare `arg0` pointer/preview；
   - 不允许进入 Base64/RC4 probe。

3. `lhs_producer_window_rejected`
   - bounded window 内没有连接点；
   - next action 指向更早/更窄的 provenance slice，而不是候选搜索。

4. `lhs_producer_hook_coverage_failed`
   - hook 未命中；
   - artifact 必须报告 hook failure 原因；
   - 不得误判为 semantic rejection。

5. project_state indexing
   - 新 artifact 被纳入 `current_state.json`；
   - bottleneck reason 更新为新分类。

## 8. Stop Conditions

Codex 本轮在以下情况停止并提交报告：

1. 找到 compare `arg0` producer。
   - 报告 producer offset、instruction、register/slot、三候选 evidence。
   - 报告是否只是 compare-side producer，还是已经接近 transform material。
   - 不要自动运行 Base64/RC4 probe，除非 gate 明确满足。

2. 找到 candidate-dependent 但不连接 compare `arg0` 的 material。
   - 分类为 unconnected。
   - 报告为什么不能作为 producer。
   - 不要围绕它重复 probe。

3. 当前 window 被排除。
   - 分类为 `lhs_producer_window_rejected`。
   - 给出下一段 bounded slice，而不是扩大搜索。

4. hook coverage 失败。
   - 报告失败原因：地址错误、inside-instruction、ASLR/base mismatch、path not reached、timeout、pointer unreadable 或 UI launch failure。
   - 不要据此推断语义。

5. 测试失败。
   - 停止并报告失败输出。
   - 不继续 harness。

本轮核心判断：compare callsite 已经解决，`arg0` 就是 LHS，`arg1` 就是 flag side。下一步只追一个问题：谁生产了 `arg0` 这个 buffer。追不到 producer，就不能进入 Base64/RC4；追到 producer，下一轮再判断它是不是 transform material。

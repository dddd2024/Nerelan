```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_compare_lhs_last_writer_provenance_20260521",
  "round_id": "round_20260521_samplereverse_compare_lhs_last_writer_provenance",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮停止 harness 工程支线，切回 `samplereverse` 逆向解题主线。

当前目标不是扩大候选搜索，也不是运行 Base64/RC4 breakpoint probe，而是追踪 `0x258c` compare 前真实 LHS buffer 的 last-writer provenance，补齐当前瓶颈 `compare_lhs_runtime_backed_writer_missing`。

## 1. Goal

当前最新样本状态显示：`0x258c` compare 已确认，`arg0` 是 candidate-dependent 的真实 LHS，`arg1` 是 flag 侧；但当前仍缺少“谁最后写入了 arg0 指向 buffer”的 runtime-backed 连接证据。

本轮目标：

```text
1. 新增一个 bounded runtime sidecar / audit，专门追踪 0x258c compare 前真实 LHS buffer 的最后写入来源。
2. 产出新 artifact：compare_lhs_last_writer_provenance_audit.json。
3. 记录 compare 前 arg0 指针、LHS buffer 快照、候选输入、写入事件、写入指令、写入地址、调用栈或上游 helper 线索。
4. 判断是否存在 runtime-backed last writer，并给出明确 classification。
5. 如果无法确认 writer，也要输出 bounded 失败原因和下一步可证伪线索。
6. 不直接推进 Base64/RC4 probe，不扩大搜索，不回旧 sample_solver。
```

建议 artifact classification：

```text
runtime_backed_last_writer_identified
writer_candidate_identified_but_not_runtime_backed
compare_reached_but_writer_missing
instrumentation_incomplete
blocked_by_environment
```

建议 artifact 顶层字段：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "run_name": "...",
  "classification": "...",
  "compare_site": "0x258c",
  "arg0_lhs_ptr": "...",
  "arg0_lhs_preview": "...",
  "candidate_input_hex": "...",
  "last_writer": {
    "instruction": "...",
    "address": "...",
    "module_offset": "...",
    "write_size": 0,
    "write_preview": "...",
    "call_stack": []
  },
  "observations": [],
  "bounded_failures": [],
  "next_allowed_probe": "..."
}
```

## 2. Current Evidence

当前任务主线：逆向解题主线，样本为 `samplereverse`。

当前 `task_packet.json` 已经是 samplereverse 派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
profile = samplereverse
sample = samplereverse
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明：

```text
1. task_packet.task 是当前样本状态派生任务，不是需要手工改写的执行入口。
2. 本轮 Codex 真正执行权威仍来自 project_state/decision_packet.md。
3. 不要手动编辑 task_packet.json；如发现 state/task/artifact 不一致，运行 project_state status 或 build 重新生成。
```

当前 live state：

```text
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
source_harness_run = sr_lhs_thread_follow_timing_20260520_r4
active_strategy = CompareAwareSearchStrategy
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.stage = compare_real_lhs_provenance_audit
```

当前 best candidates：

```text
exact2:
  candidate_hex = 78d540b49c59077041414141414141
  runtime_ci_distance5 = 246
  runtime_ci_exact_wchars = 2
  compare_semantics_agree = true

exact1/frontier:
  candidate_hex = 5a3e7f46ddd474d041414141414141
  runtime_ci_distance5 = 258
  runtime_ci_exact_wchars = 1
  compare_semantics_agree = true
```

当前已知 transform：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

但当前不是求解算法链条复述任务，而是要把真实 LHS producer 和 compare arg0 建立 runtime-backed 连接。

artifact freshness 现状：

```text
current:
  compare_probe
  compare_probe_log
  compare_real_lhs_provenance_audit
  run_manifest
  summary

stale / legacy:
  base64_rc4_static_point_discovery
  compare_handoff_return_site_probe
  compare_producer_material_confirmation
  function_semantic_audit
  frontier_summary
  guided_pool_result
  guided_pool_validation
  pairscan_summary
  smt_result
  strata_summary

missing:
  base64_rc4_breakpoint_probe
  compare_lhs_producer_audit
  compare_lhs_slot_writer_predecessor_audit
  compare_lhs_slot_writer_source_audit
  compare_lhs_upstream_writer_audit
  compare_producer_trace_probe
  dynamic_compare_path_probe
  material_hook_runtime_validation
  post_handoff_exception_unwind_audit
  pre_rc4_material_probe
```

本轮应优先消费 current artifact：

```text
solve_reports\harness_runs\sr_lhs_thread_follow_timing_20260520_r4\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
solve_reports\harness_runs\sr_lhs_thread_follow_timing_20260520_r4\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.json
solve_reports\harness_runs\sr_lhs_thread_follow_timing_20260520_r4\reports\tool_artifacts\samplereverse_patched\samplereverse_patched_compare_probe.log
```

stale artifact 只能作为背景线索，不得当作当前证据直接推进。

## 3. Do Not Do

不要做以下事情：

```text
不要继续 Phase 3 harness hardening。
不要修改 docs/phase2_harness_reproducibility_completion.md。
不要修改 harness compare/resource_budget/resume/artifact_manifest 功能。
不要手动编辑 task_packet.json。
不要手动编辑 current_state.json / artifact_index.json / negative_results.json。
不要回旧 sample_solver 盲搜。
不要只扩大 beam、topN、budget、timeout、frontier iteration。
不要使用 compare_semantics_agree=false candidates 作为 primary frontier。
不要重复 exact2 basin value-pool evaluation。
不要重复 H1/H3 fixed boundary contrast set。
不要重复当前 5-candidate transform trace consistency audit，除非新增 runtime evidence。
不要在识别 runtime-backed real LHS producer 前运行 Base64/RC4 breakpoint probe。
不要复用旧 [ebp-0x1170] 作为真实 LHS 来源，除非本轮拿到 runtime-backed provenance。
不要重复 producer material confirmation，除非新增 instruction-level evidence。
不要把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当成 Base64/RC4 material producer，除非新增语义证据。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
不要引入重型架构或新依赖。
```

## 4. Files To Inspect

必须审计：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
tests/test_compare_aware_search_strategy.py
```

必须有界读取 current artifacts：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.log
```

允许有界参考，但不得直接当 current 证据：

```text
solve_reports/tool_artifacts/samplereverse_base64_rc4_static_point_discovery_20260508/base64_rc4_static_point_discovery.json
solve_reports/tool_artifacts/samplereverse_handoff_return_outcome_manual_20260510/function_semantic_audit/function_semantic_audit.json
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 compare_real_lhs_provenance_audit.json 的 classification 是什么。
2. 该 artifact 对 0x258c compare arg0 / arg1 的结论是什么。
3. 当前真实 LHS 指针是否已确认，缺少的是 writer 还是 producer chain。
4. 现有 compare_probe.json / log 是否包含足够的 compare 前寄存器、栈、指针和 buffer 快照。
5. 现有 olly/uia sidecar 结构中是否已有可复用 hook 点和 trace 采集函数。
6. 是否已有等价 last-writer provenance artifact；如果已有，优先复用或扩展，不重复实现。
7. 为什么本轮不能直接运行 Base64/RC4 breakpoint probe。
8. 为什么旧 [ebp-0x1170] 不能直接复用。
9. 新 sidecar 的 hook 点、采样候选、停止条件和输出路径。
10. 新 sidecar 是否 bounded：只围绕 0x258c、0x2559、0x1b50、当前 best/frontier candidates，不扩大搜索。
11. 是否需要重建 project_state；若需要，只能通过 project_state build/status，不要手动编辑 task_packet。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
tests/test_compare_aware_search_strategy.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许新增：

```text
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
```

如果项目已有更合适的 olly script 命名或 sidecar helper，优先复用现有结构，不重复造入口。

允许生成 runtime artifact，但不要提交完整 solve_reports：

```text
solve_reports/harness_runs/<run_name>/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
```

允许归档：

```text
project_state/rounds/round_20260521_samplereverse_compare_lhs_last_writer_provenance/*
```

不要修改：

```text
reverse_agent/harness.py
reverse_agent/project_state.py
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/schema.md
docs/phase2_harness_reproducibility_completion.md
```

如确需刷新 project_state，只能运行：

```powershell
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
```

并在 report 中说明原因。不要手动编辑 state JSON。

### 6.1 Sidecar behavior

新 sidecar 应围绕以下点做 bounded trace：

```text
compare site: 0x258c
post_handoff_lhs_reload / compare producer candidate: 0x2559
handoff helper candidate: 0x1b50
current best candidates:
  78d540b49c59077041414141414141
  5a3e7f46ddd474d041414141414141
```

建议采集：

```text
1. 到达 0x258c 前的 arg0 / arg1。
2. arg0 指针指向 buffer 的 preview。
3. 0x2559 处 reload 的来源寄存器、内存地址、值。
4. 0x1b50 enter/return 期间与 arg0 buffer 相关的写入事件。
5. 对 arg0 buffer 范围设置 watch / memory write trace，如当前工具链支持。
6. 采集少量调用栈或 return-site 线索。
```

如果 Olly/automation 无法直接 watch memory writes，必须退化为 bounded instruction-window trace，并在 artifact 中写明：

```text
classification = instrumentation_incomplete
bounded_failures 包含 missing watchpoint support 或 equivalent reason
```

### 6.2 Artifact output rules

新 artifact 必须：

```text
1. JSON 可读。
2. 顶层包含 classification。
3. 顶层包含 compare_site、candidate_input_hex、arg0_lhs_ptr、arg0_lhs_preview。
4. 如果找到 writer，包含 last_writer.instruction / address / module_offset / write_size / write_preview。
5. 如果没有找到 writer，包含 bounded_failures 和 next_allowed_probe。
6. 不包含大块 memory dump。
7. 不包含本机绝对路径作为唯一 provenance。
```

### 6.3 Report binding requirement

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_samplereverse_compare_lhs_last_writer_provenance_20260521",
  "round_id": "round_20260521_samplereverse_compare_lhs_last_writer_provenance",
  "based_on_decision_id": "decision_samplereverse_compare_lhs_last_writer_provenance_20260521",
  "status": "SUCCESS",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

如果 runtime 环境阻塞，应使用：

```text
status = BLOCKED 或 PARTIAL
acceptance_recommendation = BLOCKED 或 NEEDS_REVIEW
```

不要把未实际运行 runtime sidecar 的任务报告为 SUCCESS。

## 7. Tests

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\strategies\compare_aware_search.py
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

如果新增 Olly script：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_lhs_last_writer_provenance.py
```

如果 runtime 环境可用，必须运行 bounded sidecar 或对应 harness profile，并记录：

```text
run_name
candidate_input_hex
artifact path
classification
是否到达 0x258c
是否确认 runtime-backed writer
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260521_samplereverse_compare_lhs_last_writer_provenance
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向上一轮 Phase 2 matrix fix 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK 或给出明确 BLOCKED/PARTIAL 原因。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要回旧 sample_solver。
2. 需要只靠扩大 beam/budget 才能推进。
3. 需要在 real LHS producer 识别前运行 Base64/RC4 breakpoint probe。
4. 需要把 stale artifact 当作 current evidence。
5. 需要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
6. 需要读取或提交完整 solve_reports。
7. 需要使用 compare_semantics_agree=false candidate 作为主线。
8. 需要重复 negative_results 中已经禁止的 exact2 basin 或 H1/H3 contrast 方向。
9. 无法到达 0x258c compare。
10. 无法采集 arg0 LHS pointer 或 buffer preview。
11. runtime watchpoint / write trace 不可用，且无法退化为 bounded instruction-window trace。
12. 无法让 report.based_on_decision_id 绑定当前 decision_id。
13. 无法让 pytest_result.txt 记录真实测试和 runtime/blocked 状态。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. decision/report 绑定当前 decision_id。
2. 没有继续 harness Phase 3 工作。
3. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
4. 没有运行 Base64/RC4 breakpoint probe。
5. 没有回旧 solver 或扩大搜索。
6. 新增或复用 bounded last-writer provenance sidecar。
7. 生成 compare_lhs_last_writer_provenance_audit.json，或明确 BLOCKED/PARTIAL 原因。
8. artifact 顶层 classification 清楚。
9. 到达 0x258c 的事实、arg0 LHS pointer、buffer preview 被记录。
10. 如果确认 writer，必须是 runtime-backed；如果没有确认，必须解释缺口。
11. tests / py_compile / lint-decision / lint-report / lint-handoff 被真实记录。
12. 不提交完整 solve_reports。
```

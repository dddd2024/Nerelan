```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_reverse_arg0_raw_write_gap_audit",
  "round_id": "round_20260524_reverse_arg0_raw_write_gap_audit",
  "based_on_state_build_id": "state_20260524_115510_fd9f1dbf2897",
  "based_on_state_digest": "fd9f1dbf2897e27c3d377625bf5b519dfa624fba2952acc72e65953338091eee",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续**逆向解题主线**，不是工程架构改造支线。不要继续 skill、registry、sync、agent runtime 或 Phase 2 closeout 类工作。

当前 `task_packet.task` / `task_packet.derived_task` 仍是 `Improve compare lhs last-writer instrumentation`，但该字段只是由样本状态派生出的建议任务；当前轮 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。

上一轮已经把 `compare_real_lhs_provenance_audit` 的 writer blocker 结构化到 project_state。当前新的瓶颈不再是“字段缺失”，而是：当前 run 中确实捕获到 raw write events，但这些 writes 没有覆盖实际 compare `arg0` 指向的 LHS buffer。

## 1. Goal

本轮目标：解释并固定分类当前 `raw_writes_not_intersecting_arg0` 卡点。

具体目标：

```text
1. 从 project_state/artifact_index.json 的 latest_artifacts_v2 出发，只读取 freshness=current 的 compare_real_lhs_provenance_audit artifact。
2. 对该 artifact 中 actual_compare.arg0_value_by_candidate、arg0_preview_by_candidate、write_monitor_health、last_writer_summary.missing_candidate_reasons、nearest_non_intersecting_writes 做有界审计。
3. 建立 raw write address/window 与 actual compare arg0 address/window 的差距表，按 candidate 输出：
   - actual_arg0 address / preview prefix
   - nearest write address
   - distance_to_arg0
   - bounded_failure_reason
   - instruction/module_offset
   - sequence/thread/event provenance if present
4. 判断当前 blocker 属于哪一种：
   - write_monitor_target_window_wrong：监控的是错误地址窗口；
   - arg0_pointer_origin_untracked：真实 arg0 pointer 来源没有被监控；
   - intersection_window_miscalculated：artifact 中已有应相交写入但聚合窗口计算错误；
   - writer_event_schema_gap：sidecar 输出了写入但字段不足以确认相交关系；
   - no_runtime_writer_before_compare：当前 hook 范围内确实没有真实 arg0 writer。
5. 如果只是 aggregation/window 计算错误，做最小修复并补测试。
6. 如果证据显示真实 arg0 来源未被监控，只新增一个 bounded diagnostic 字段或 bounded sidecar hook 设计，不要扩大搜索，不要跑 Base64/RC4 probe。
```

本轮不求最终 flag，不做 candidate search，不扩大 frontier，不扩大 runtime budget。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 project_state 基础：

```text
state_build_id = state_20260524_115510_fd9f1dbf2897
based_on_state_digest = fd9f1dbf2897e27c3d377625bf5b519dfa624fba2952acc72e65953338091eee
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.blocker = raw_writes_not_intersecting_arg0
```

`task_packet.task` 和 `task_packet.derived_task` 是 `Improve compare lhs last-writer instrumentation`，但这是派生建议，不是当前轮权威。当前轮权威是本 `decision_packet.md`。

当前 artifact freshness：

```text
latest_harness_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_probe.freshness = current
latest_artifacts_v2.run_manifest.freshness = current
latest_artifacts_v2.summary.freshness = current
```

已知当前 artifact 结论：

```text
classification = compare_lhs_runtime_backed_writer_missing
runtime_backed_count = 3
write_monitor_health.enabled = true
write_monitor_health.raw_write_count = 27
write_monitor_health.filtered_intersecting_write_count = 0
last_writer_summary.raw_write_event_count = 27
last_writer_summary.retained_write_count = 0
last_writer_candidates = []
missing_candidate_reasons = raw_writes_observed_but_none_intersect_actual_arg0
lhs_writer_classification_blocker = raw_writes_not_intersecting_arg0
```

当前 actual compare evidence：

```text
actual_compare.lhs_side = arg0
actual_compare.flag_side = arg1
actual_compare.arg0_candidate_dependent = true
actual_compare.arg1_candidate_dependent = false
actual_compare.entry = 0x258c
```

重要限制：`compare_probe` fallback 只能证明 actual compare arg0/arg1，不等于 writer provenance。旧 `[ebp-0x1170]` 已被当前 artifact 拒绝，不能复用为真实 LHS source。

当前 skill_profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

`.codex-skills/registry.json` 当前只登记这两个 active skill。不要增加 skill。

## 3. Do Not Do

不要做以下事情：

```text
不要继续工程支线或 Phase 2 skill 改造。
不要修改 .codex-skills/、registry、sync 或 audit 工具。
不要默认读取完整 solve_reports/。
不要默认读取 PROJECT_PROGRESS_LOG.txt。
不要运行 Base64/RC4 breakpoint probe。
不要运行 Base64/RC4 probe 的任何变体。
不要回 old sample_solver blind search。
不要扩大 beam / topN / budget / timeout / frontier iteration。
不要新增 candidate search。
不要把 compare_semantics_agree=false candidates 作为 primary frontier。
不要提交完整 solve_reports。
不要把 stale / missing artifact 当 current evidence。
不要把 compare_probe fallback args 当 writer provenance。
不要复用旧 [ebp-0x1170] 作为真实 LHS source，除非当前 artifact 给出新的 runtime-backed provenance。
不要把 0x4019e0、0x401b50、0x4018cd、0x401be3 直接称为 Base64/RC4 producer，除非本轮产生新的语义证据。
不要为了推进而伪造 runtime-backed writer。
```

必须遵守 `project_state/negative_results.json`，尤其是：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
rerun Base64/RC4 breakpoint probe before confirming a Base64/RC4 instruction hook
repeat producer material confirmation without adding instruction-level evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
run Base64/RC4 breakpoint probe before real lhs producer identification
```

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取的 artifact：

```text
project_state/artifact_index.json 中 latest_artifacts_v2["compare_real_lhs_provenance_audit"].path
```

可有界读取：

```text
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/summary.json
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/run_manifest.json
```

仅当需要确认当前 artifact schema 或 case result provenance 时，才允许读取：

```text
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/case_results/samplereverse-compare-producer-backtrace.json
```

不要默认读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史 rounds 下的完整大文件
.codex-skills/**
```

## 5. Required Audit

Codex 修改前必须完成并在 report 中记录：

```text
1. 确认本 decision_meta：decision_id=decision_20260524_reverse_arg0_raw_write_gap_audit，status=APPROVED，mainline=reverse_solving。
2. 确认 skill_profiles 为 reverse-agent-iteration@v2 和 samplereverse-frontier@v2。
3. 确认 task_packet.task / derived_task 只是派生建议，当前执行权威是 decision_packet.md。
4. 确认 artifact_index.latest_artifacts_v2.compare_real_lhs_provenance_audit 的 freshness=current，source_run=sr_lhs_hook_observation_reliability_20260524_r4。
5. 有界读取 current compare_real_lhs_provenance_audit artifact。
6. 对 3 个 candidate 分别列出 actual_arg0、arg0 preview、nearest_non_intersecting_writes、distance_to_arg0、bounded_failure_reason。
7. 判断 raw writes 与 actual arg0 不相交是因为：地址窗口错误、真实 pointer 来源未监控、窗口计算错误、schema gap，还是 hook 范围内确实没有 writer。
8. 审计 compare_aware_search.py 中 intersection/window/filtering/summary 派生逻辑。
9. 审计 compare_pre_compare_handoff_target_probe.py 中 write monitor 的 target address/window 来源，确认它当前到底监控了哪个范围。
10. 确认本轮没有运行 Base64/RC4 probe、old solver、candidate search、beam/budget 扩张。
```

报告中必须明确回答：

```text
raw write events 是写到了哪里？
actual compare arg0 指向哪里？
二者不相交是预期、计算错误，还是监控目标错误？
下一步如果需要 runtime sidecar，最小 hook 点是什么？为什么不是 Base64/RC4 probe？
```

## 6. Implementation Scope

### Phase A：只读证据表

先不改代码，先生成一张证据表并写入 report：

```text
candidate_hex
actual_arg0
actual_arg0_preview_prefix
nearest_write_address
nearest_write_module_offset
nearest_write_instruction
nearest_write_sequence
distance_to_arg0
bounded_failure_reason
same_thread / thread_id if present
write_size / write_preview if present
```

如果 artifact 缺字段，记录 schema gap，不要猜。

### Phase B：聚合/窗口计算审计

审计并判断：

```text
1. actual arg0 window 的 start/end/length 是否按真实 compare count 计算。
2. raw write event address/size/end 是否正确解析。
3. overlap 判断是否包含边界条件。
4. nearest_non_intersecting_writes 是否按真实距离排序。
5. filtered_intersecting_write_count=0 是否由数据真实导致，而不是字段名或类型转换导致。
```

如果发现纯代码 bug，允许最小修改：

```text
reverse_agent/strategies/compare_aware_search.py
```

并补对应单元测试。

### Phase C：sidecar 诊断补强，仅在必要时执行

如果 Phase A/B 证明聚合逻辑正确，而 sidecar 当前监控的是错误窗口或没有跟踪 actual arg0 pointer 来源，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
```

允许新增的诊断字段仅限：

```text
arg0_window
raw_write_window_summary
nearest_non_intersecting_write_summary
write_monitor_target_source
actual_arg0_pointer_origin_status
arg0_pointer_origin_gap_reason
recommended_next_hook_points
```

禁止新增大范围 hook、禁止扫描全内存、禁止扩大 candidate set、禁止扩大搜索预算。

### Phase D：project_state 投影，必要时执行

如果新增了稳定诊断字段，允许最小更新：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

目标只是把 blocker 投影得更清楚，例如：

```text
current_bottleneck.blocker = arg0_pointer_origin_untracked
current_bottleneck.blocker = write_monitor_target_window_wrong
current_bottleneck.blocker = intersection_window_miscalculated
```

不要把动态事实写入 skill。

### Phase E：bounded harness rerun，默认不执行

默认不运行 harness。只有当改动了 sidecar 输出字段，并且单元测试无法证明 artifact schema 时，才允许一次 bounded harness rerun。

如必须运行，run-name 必须是新的、明确的：

```text
sr_arg0_raw_write_gap_audit_20260524_r1
```

限制：

```text
只使用当前 samplereverse sample。
只使用当前 fixed candidates / current strategy。
不得扩大 beam / topN / budget / timeout。
不得运行 Base64/RC4 probe。
不得提交完整 solve_reports。
```

### Phase F：报告与状态

本轮结束必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 project_state 派生逻辑或 artifact schema 有变化，运行：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如果没有运行 harness，仍应说明使用的 selected run 是 `sr_lhs_hook_observation_reliability_20260524_r4`，并说明没有产生新的 runtime artifact。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or raw_write or last_writer or provenance or classification"
python -m pytest -q tests/test_project_state.py -k "artifact or provenance or bottleneck or decision or report"
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 `reverse_agent/project_state.py`，必须补充：

```bash
python -m pytest -q tests/test_project_state.py
```

如果修改了 sidecar 或 artifact schema，必须补充至少一个不依赖真实 harness 的 fixture/unit test，覆盖：

```text
raw writes exist but all are before/outside actual arg0 window
nearest_non_intersecting_writes are retained in summary
actual arg0 pointer is runtime-backed but writer provenance is absent
compare_probe fallback must not promote writer provenance
```

如果运行 project_state build，必须补充：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如运行 harness，必须记录完整命令和 run-name，并说明为什么单元测试不足。

不需要运行：

```bash
full unrelated pytest suite
Base64/RC4 breakpoint probe
old sample_solver
full solve_reports scan
PROJECT_PROGRESS_LOG read
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. compare_real_lhs_provenance_audit artifact 缺失或 freshness 不是 current。
2. current artifact 与 current_state 的 bottleneck/blocker 冲突，且无法解释。
3. 必须读取完整 solve_reports 才能继续。
4. 必须读取完整 PROJECT_PROGRESS_LOG.txt 才能继续。
5. 必须运行 Base64/RC4 probe、old solver、beam/budget 扩张或 candidate search 才能继续。
6. 无法区分 actual compare arg0 evidence 与 writer provenance。
7. 需要新增大范围 memory scan / global hook 才能继续。
8. 需要修改 .codex-skills 或 registry 才能继续。
9. 测试无法运行且没有环境原因。
10. 代码改动会把 stale/missing artifact 当 current evidence。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_reverse_arg0_raw_write_gap_audit",
  "round_id": "round_20260524_reverse_arg0_raw_write_gap_audit",
  "based_on_decision_id": "decision_20260524_reverse_arg0_raw_write_gap_audit",
  "status": "SUCCESS / PARTIAL / FAILED / BLOCKED",
  "acceptance_recommendation": "ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": []
}
```

报告正文必须包含：

```text
1. current artifact path/source_run/freshness。
2. 3 个 candidate 的 arg0/write gap evidence table。
3. raw writes 与 actual arg0 不相交的分类结论。
4. 是否发现 aggregation/window 计算 bug。
5. 是否修改 sidecar；如果修改，新增字段和原因。
6. 是否运行 harness；默认应为 no。
7. 是否产生新 artifact；如果没有，说明仍基于 current selected run。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- current artifact freshness 被正确核验。
- raw write vs actual arg0 gap 被按 candidate 清楚解释。
- 如果是计算/aggregation bug，已最小修复并测试。
- 如果是真实 pointer origin 未监控，已给出最小下一 hook 点或诊断字段，不伪造 writer。
- 未运行禁止 probe，未扩大搜索。
- tests 通过。

ACCEPTED_WITH_LIMITATIONS：
- 完成 gap 审计和 blocker 分类，但没有运行 harness 或没有新增 runtime artifact。
- 结论能指导下一轮 bounded hook，而不是回到旧 solver/RC4/Base64。

REWORK_REQUIRED：
- 把 stale artifact 当 current evidence。
- 把 compare_probe fallback 当 writer provenance。
- 未读取 current artifact 就修改分类逻辑。
- 运行 Base64/RC4 probe、old solver 或扩大搜索预算。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- current artifact 缺失且无法 rebuild。
- project_state 与 artifact_index 严重冲突。
- 必要测试无法运行。
```

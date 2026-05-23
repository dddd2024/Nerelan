```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_samplereverse_lhs_last_writer_instrumentation",
  "round_id": "round_20260523_samplereverse_lhs_last_writer_instrumentation",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于**逆向解题主线**，不是工程架构改造支线。

工程 closeout correction 已完成，当前 active report 为：

```text
report_id = report_20260523_engineering_closeout_record_correction
round_id = round_20260523_engineering_closeout_record_correction
based_on_decision_id = decision_20260523_engineering_closeout_record_correction
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

下一轮回到 `samplereverse`，目标是有界修复/增强 compare LHS last-writer instrumentation，生成新的 runtime-backed evidence。不要扩大搜索，不要跑 Base64/RC4 breakpoint probe，不要回旧 solver。当前瓶颈是 `compare_real_lhs_provenance_audit` 的 `compare_lhs_runtime_backed_writer_missing`。

## 1. Goal

本轮目标：

```text
1. 回到 samplereverse 逆向解题主线。
2. 修复或增强 compare_real_lhs_provenance_audit 的 last-writer instrumentation。
3. 针对 0x258c compare 前真实 LHS arg0 buffer，捕获“最后一次写入 arg0 指向 buffer 的 writer”。
4. 新增或刷新 artifact：
   compare_lhs_last_writer_provenance_audit.json
   或在现有 compare_real_lhs_provenance_audit.json 中补齐 last_writer_summary / last_writer_candidates / write_monitor_health。
5. 目标证据至少包含：
   - actual compare entry 已确认；
   - lhs_side=arg0；
   - flag_side=arg1；
   - lhs_preview_varies_by_candidate=True；
   - last_writer runtime-backed；
   - writer intersects actual compare arg0 buffer；
   - writer after_preview_matches_arg0 或能解释写入后的 arg0 preview；
   - candidate_dependent 字段明确；
   - breakpoint_probe_allowed=False，除非发现真正 material producer 且有新证据。
6. 更新 project_state，使 task_packet/current_state 能反映新的 last-writer 结论。
```

本轮不是求解 flag，不做候选空间扩展；只补缺失的 runtime provenance 证据。

## 2. Current Evidence

当前任务主线判断：**逆向解题主线**。

`task_packet.json` 显示：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
state_build_id = state_20260520_052928_8a77e6637c6c
state_scope = sample_state
execution_scope = decision_packet_controls_current_round
```

这说明 `task_packet.task` 在本轮不再只是工程支线干扰项，而是当前逆向主线的合理 derived_task；但 Codex 执行权威仍必须以本 `decision_packet.md` 为准。

当前 `current_state.json` 仍是 sample evidence state：

```text
active_strategy = CompareAwareSearchStrategy
current_mainline = L15(prefix8)
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
known_transform = input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

`current_state` 中的 function semantics 仍表明若干函数不能直接当成 Base64/RC4 material producer，尤其 `0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3` 不能在没有新语义证据时直接提升为 material producer。

当前 `artifact_index.latest_artifacts_v2` 中：

```text
compare_probe = current
compare_probe_log = current
compare_real_lhs_provenance_audit = current
base64_rc4_static_point_discovery = stale
compare_handoff_return_site_probe = stale
compare_producer_material_confirmation = stale
大量 compare_lhs_* / compare_esi_* / material_hook_runtime_validation artifact = missing
```

因此，本轮只允许基于 `current` 的 compare probe / real lhs provenance 继续做有界 instrumentation，不要把 stale artifact 当成当前证据。

工程支线 closeout 已完成：

```text
report_20260523_engineering_closeout_record_correction = SUCCESS
pytest_result_summary.status = PASSED
correction round archived cleanly
```

所以本轮无需继续工程 closeout。

## 3. Do Not Do

不要做以下事情：

```text
不要回 old sample_solver blind search。
不要只增加 guided_pool beam 或 budget。
不要扩大 topN / timeout / frontier iteration。
不要使用 compare_semantics_agree=false candidates 作为主 frontier。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要读取 PROJECT_PROGRESS_LOG.txt。
不要运行 Base64/RC4 breakpoint probe。
不要把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当成 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
不要复用旧 [ebp-0x1170] 作为真实 LHS 证据。
不要重复 producer material confirmation，除非新增 instruction-level evidence。
不要重复 compare return-site audit，除非明确消费其已有 classification。
不要修改工程支线 closeout / archive policy。
不要修改 project_state closeout 逻辑。
不要修改 PROJECT_PROGRESS_LOG.txt。
不要引入数据库、调度平台、外部服务或重型依赖。
```

还要避免重复 negative_results 中已禁止方向：

```text
不要回 old sample_solver blind search。
不要只增加 guided_pool beam 或 budget。
不要使用 compare_semantics_agree=false candidates 作为主 frontier。
不要提交完整 solve_reports。
不要重复 Base64/RC4 breakpoint probe。
不要复用旧 [ebp-0x1170] 作为真实 LHS 证据。
```

## 4. Files To Inspect

必须检查：

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界检查当前 artifact 引用，不要扫完整 `solve_reports`：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/run_manifest.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/summary.json
```

必要时检查：

```text
reverse_agent/function_semantics.py
reverse_agent/ida_scripts/*
reverse_agent/olly_scripts/*
```

但只在确认 instrumentation 脚本位置需要修改时检查。不要默认大范围读 `olly_scripts`。

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史 project_state/rounds/* 全量目录
```

## 5. Required Audit

Codex 修改前必须先完成并在报告中记录以下审计：

```text
1. 读取当前 decision_meta，确认本轮 decision_id 是 decision_20260523_samplereverse_lhs_last_writer_instrumentation。
2. 读取 task_packet，确认 current_bottleneck.stage/reason。
3. 读取 current_state，确认 active_strategy=CompareAwareSearchStrategy。
4. 读取 artifact_index.latest_artifacts_v2，确认：
   - compare_probe freshness=current
   - compare_real_lhs_provenance_audit freshness=current
   - Base64/RC4 breakpoint probe missing
   - 关键 compare_lhs_* 新 artifact missing
5. 有界读取 compare_real_lhs_provenance_audit.json，确认：
   - actual_compare 是否确认；
   - lhs_side 是否为 arg0；
   - last_writer 当前缺失或不完整；
   - write monitor 是否存在 health / missing candidate / missed write 线索。
6. 有界读取 compare_probe.json，确认 compare site 和 candidate set。
7. 检查 negative_results，确认本轮不会重复禁止方向。
8. 明确说明本轮不需要完整 solve_reports。
9. 明确说明本轮不会运行 Base64/RC4 breakpoint probe。
```

## 6. Implementation Scope

### Phase A：定位 last-writer instrumentation 缺口

先只审计现有 instrumentation，不急着改搜索逻辑。

要求 Codex 找到现有 compare real LHS provenance 逻辑中以下信息来源：

```text
actual compare arg0 pointer 如何取得；
arg0 buffer range 如何定义；
写监控 watch range 如何设置；
写事件如何过滤；
线程 follow 是否正确；
候选输入与写事件如何关联；
最后写入如何选择；
after_preview 如何采集；
candidate_dependent 如何计算；
missing candidate 的原因如何记录。
```

如果发现现有 watch range 太窄、线程跟踪缺失、write filter 错误、只监控旧 frame anchor，则只修 instrumentation，不扩展候选搜索。

### Phase B：实现有界 last-writer provenance audit

允许做以下修改：

```text
1. 在 CompareAwareSearchStrategy 相关 sidecar 中新增或修复 last-writer audit。
2. 新增 artifact 文件名常量，例如：
   compare_lhs_last_writer_provenance_audit.json
3. 每个候选只监控 compare 前 arg0 指向 buffer 的有限窗口。
4. 只跟踪当前 runtime-backed candidate set，不扩展 beam/topN。
5. 记录 last_writer_candidates，字段至少包含：
   - candidate_hex
   - compare_callsite 或 caller_module_offset
   - arg0_ptr
   - write_address
   - write_size
   - writer_module_offset
   - writer_instruction 如可得
   - before_preview_hex
   - after_preview_hex
   - compare_arg0_preview_hex
   - after_preview_matches_arg0
   - candidate_dependent
   - thread_id
   - hit_count
6. 记录 write_monitor_health，字段至少包含：
   - enabled
   - candidate_count
   - followed_thread_count
   - raw_write_count
   - filtered_intersecting_write_count
   - missing_candidate_count
   - missing_candidates
7. 记录 summary：
   - classification
   - runtime_backed_count
   - connects_to_actual_arg0
   - candidate_dependent
   - breakpoint_probe_allowed
   - next_bounded_action
```

建议 classification 取值：

```text
last_writer_identified
writer_path_observed_but_unconnected
instrumentation_incomplete
compare_lhs_runtime_backed_writer_missing
```

只有当 `last_writer_identified` 且 writer 连接到 actual compare arg0 时，下一轮才允许考虑 material hook validation。仍不允许直接跑 Base64/RC4 breakpoint probe。

### Phase C：project_state 集成

如果新增 artifact：

```text
compare_lhs_last_writer_provenance_audit.json
```

则必须更新：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/artifact_index.json
project_state/current_state.json
project_state/task_packet.json
project_state/negative_results.json
```

要求：

```text
1. artifact_index.latest_artifacts / latest_artifacts_v2 能索引新 artifact。
2. current_state 能摘要 latest_compare_lhs_last_writer_provenance_audit。
3. current_bottleneck 能根据 classification 更新：
   - last_writer_identified -> Validate bounded material hook from confirmed compare lhs last writer
   - instrumentation_incomplete -> Improve compare lhs last-writer instrumentation
   - writer_path_observed_but_unconnected -> Trace writer-to-arg0 connection
4. negative_results 能阻止重复无效方向，例如：
   repeat last-writer audit without fixing instrumentation gap
```

如果不新增 artifact，而是增强现有 `compare_real_lhs_provenance_audit.json`，也必须让 `current_state` 能暴露 last_writer_summary / last_writer_candidates / write_monitor_health。

### Phase D：运行有界 harness

只允许运行与本轮 last-writer provenance 相关的有界命令。

允许：

```bash
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "last_writer or real_lhs or provenance"
python -m pytest -q tests/test_project_state.py -k "last_writer or provenance or artifact"
```

允许在本地运行一个 bounded sidecar/harness，用于当前 selected candidate set 的 compare LHS last-writer audit。

不允许：

```bash
Base64/RC4 breakpoint probe
full frontier expansion
old sample_solver
blind search
beam/budget/topN expansion
完整 solve_reports scan
```

### Phase E：刷新 project_state

若生成了新 artifact，必须运行或等价执行：

```bash
python -m reverse_agent.project_state build --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果 build 无法自动选中新 run，Codex 必须指定对应 run name，避免 artifact_index 混入旧 run：

```bash
python -m reverse_agent.project_state build --state-dir project_state --run-name <new_run_name>
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "last_writer or real_lhs or provenance"
python -m pytest -q tests/test_project_state.py -k "last_writer or provenance or artifact"
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 `reverse_agent/project_state.py`，必须额外运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
```

如果运行了 bounded harness/sidecar，报告中必须记录：

```text
run_name
generated artifact path
candidate_count
runtime_backed_count
classification
best/representative last_writer_candidates
```

不需要运行：

```bash
tests/test_sidecar_health.py
Base64/RC4 breakpoint probe
完整 harness sweep
```

除非 Codex 修改了相关文件；若修改，必须说明原因并补测。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. 当前 decision_packet.md 缺失 decision_meta。
2. compare_real_lhs_provenance_audit.json 缺失且 artifact_index 没有 current 替代证据。
3. compare_probe 不是 current，且无法从 latest_artifacts_v2 确认当前 compare site。
4. 需要读取完整 solve_reports 才能定位问题。
5. 需要运行 Base64/RC4 breakpoint probe 才能继续。
6. 需要扩大 beam/budget/topN 才能继续。
7. 需要回 old sample_solver。
8. 需要把 compare_semantics_agree=false candidates 作为主 frontier。
9. 需要复用旧 [ebp-0x1170] 作为真实 LHS 来源。
10. last-writer watch range 无法绑定 actual compare arg0。
11. 线程跟踪无法确认，导致写事件可能来自错误线程。
12. 新 artifact 无法被 project_state 索引。
13. 本轮 diff 超过 500 行，且主要不是 instrumentation + tests + project_state artifact wiring。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260523_samplereverse_lhs_last_writer_instrumentation",
  "round_id": "round_20260523_samplereverse_lhs_last_writer_instrumentation",
  "based_on_decision_id": "decision_20260523_samplereverse_lhs_last_writer_instrumentation",
  "status": "SUCCESS / PARTIAL / FAILED / BLOCKED",
  "acceptance_recommendation": "ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": []
}
```

报告正文必须明确记录：

```text
1. 是否生成 compare_lhs_last_writer_provenance_audit.json 或增强 compare_real_lhs_provenance_audit.json。
2. classification。
3. runtime_backed_count。
4. last_writer_summary。
5. write_monitor_health。
6. 是否连接 actual compare arg0。
7. 是否 candidate-dependent。
8. 是否仍禁止 Base64/RC4 breakpoint probe。
9. 真实测试命令和结果。
10. project_state build/status/lint-report 结果。
11. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- 生成 current last-writer provenance evidence。
- last_writer runtime-backed，且能连接 actual compare arg0。
- project_state 能索引并摘要该证据。
- tests 通过。
- 未违反 negative_results。
- 未运行 Base64/RC4 breakpoint probe。
- 未扩大搜索。

ACCEPTED_WITH_LIMITATIONS：
- instrumentation 明显改善，能解释 missing writer 原因，但仍未识别 writer。
- project_state 正确记录 instrumentation_incomplete 或 writer_path_observed_but_unconnected。
- 没有越界运行禁止 probe。

REWORK_REQUIRED：
- 重复旧 audit 但没有新增证据。
- 把 stale artifact 当 current。
- 复用旧 [ebp-0x1170] 当真实 LHS。
- 运行 Base64/RC4 breakpoint probe。
- 扩大 beam/budget/topN。
- 报告和 decision_id 不匹配。

BLOCKED：
- current compare artifacts 缺失或不可读。
- 无法确定 actual compare arg0。
- 环境无法运行有界 sidecar/harness。
```

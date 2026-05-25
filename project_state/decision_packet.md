```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260525_reverse_arg0_bounded_writer_rerun",
  "round_id": "round_20260525_reverse_arg0_bounded_writer_rerun",
  "based_on_state_build_id": "state_20260525_085052_26b80fabb7fe",
  "based_on_state_digest": "26b80fabb7feee513ef3b3e94bc799e4242613b7d0c25938d4ae46b2e965ab95",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **逆向解题主线**，不是工程架构改造支线。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`，不是 `project_state/task_packet.json` 中的 `task` 或 `derived_task`。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`：Codex 已经完成 `arg0_final_data_writer_trace` 的 sidecar schema / strategy aggregation / project_state projection / focused tests，但没有运行新的 bounded harness，也没有产生新的 runtime artifact。当前 blocker 是 `arg0_final_writer_trace_schema_gap`。本轮任务是使用上一轮新增字段做一次固定 candidates 的 bounded sidecar rerun，采集 `0x253a / 0x2559 / 0x258b / 0x258c` 的 runtime-backed rows，验证是否能把 schema gap 推进为 pointer chain 或 final data writer 证据。

## 1. Goal

本轮目标：只针对 current samplereverse fixed candidates 执行一次 bounded runtime sidecar rerun，使用上一轮新增的 `arg0_final_data_writer_trace_point` 字段，采集并聚合 actual compare `arg0` 的最小 writer-trace 证据。

必须回答：

```text
1. module+0x258c actual compare callsite 是否 runtime-backed 观测到 actual arg0。
2. module+0x258b pre-push ESI 是否 runtime-backed 观测到，且 ESI 是否等于 actual arg0。
3. module+0x2559 reload source/value 是否 runtime-backed 观测到，且 reload value 是否等于 actual arg0。
4. module+0x253a slot writer 是否 runtime-backed 观测到，且 slot writer value 是否能连接到 0x2559/0x258b/0x258c pointer chain。
5. write ring 是否观察到写入 actual_arg0 指向 buffer 的 data write。
6. 如果出现 data write，write range 是否 intersects actual_arg0 compare window。
7. 如果仍未发现 final data writer，缺口应分类为：
   - arg0_pointer_chain_identified_writer_missing
   - arg0_final_writer_not_observed_in_bounded_window
   - arg0_writer_trace_runtime_blocked
   - arg0_final_writer_trace_schema_gap
```

本轮不求最终 flag，不做 candidate search，不扩大 frontier，不扩大 runtime budget，不进入 Base64/RC4 probe。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 state 基础：

```text
state_build_id = state_20260525_085052_26b80fabb7fe
state_digest = 26b80fabb7feee513ef3b3e94bc799e4242613b7d0c25938d4ae46b2e965ab95
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.blocker = arg0_final_writer_trace_schema_gap
```

`task_packet.task` / `task_packet.derived_task` 当前只是派生建议。当前轮执行权威是本 `project_state/decision_packet.md`。

当前 artifact freshness：

```text
latest_harness_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_lhs_hook_observation_reliability_20260524_r4
latest_artifacts_v2.compare_probe.freshness = current
latest_artifacts_v2.run_manifest.freshness = current
latest_artifacts_v2.summary.freshness = current
```

当前 actual compare evidence：

```text
candidate 78d540b49c59077041414141414141 -> actual_arg0 = 0x35cd018, preview_prefix = 46006c004464830d311c7010
candidate 5a3e7f46ddd474d041414141414141 -> actual_arg0 = 0x378cfd8, preview_prefix = 460061357f0b8c688502de32
candidate 78d540b49c59076f41414141414141 -> actual_arg0 = 0x421d018, preview_prefix = d6707f3ad7f8bb0e0fd64fcb
actual_compare.entry = module+0x258c
actual_compare.lhs_side = arg0
actual_compare.flag_side = arg1
actual_compare.arg0_candidate_dependent = true
actual_compare.arg1_candidate_dependent = false
```

上一轮新增 projection 的关键状态：

```text
latest_compare_real_lhs_provenance_audit.arg0_final_data_writer_trace.classification = final_writer_trace_schema_gap
final_writer_status = final_writer_trace_schema_gap
pointer_carrier_is_final_writer = false
pointer_write_is_final_data_writer = false
rows[*].final_writer_gap_reason = bounded_pointer_chain_rows_missing
rows[*].nearest_write_intersects_arg0 = false
recommended_next_hook_points = module+0x253a, module+0x2559, module+0x258b, module+0x258c
```

当前缺口：

```text
0x253a / 0x2559 / 0x258b 缺 runtime-backed row。
当前 write ring raw_write_count=27，但 filtered_intersecting_write_count=0。
当前 last_writer_candidates=[]。
当前不能把 pointer carrier 或 pointer write 伪称 final data writer。
```

当前 skill_profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

## 3. Do Not Do

不要做以下事情：

```text
不要继续工程支线或 skill 改造。
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
不要把 pointer carrier 伪称为 final data writer。
不要把 slot pointer write 伪称为 buffer data write。
不要无条件复用旧 [ebp-0x1170] 作为真实 LHS source。
不要把 0x4019e0、0x401b50、0x4018cd、0x401be3 直接称为 Base64/RC4 producer，除非本轮产生新的 runtime-backed 语义证据。
不要为了推进而伪造 final writer。
不要再次只改 schema/projection 而不运行 bounded sidecar rerun，除非 runtime 环境阻断并在 report 中说明。
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
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取的 current artifacts：

```text
project_state/artifact_index.json 中 latest_artifacts_v2["compare_real_lhs_provenance_audit"].path
project_state/artifact_index.json 中 latest_artifacts_v2["compare_probe"].path
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/summary.json
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/run_manifest.json
```

允许有界读取：

```text
solve_reports/harness_runs/sr_lhs_hook_observation_reliability_20260524_r4/case_results/samplereverse-compare-producer-backtrace.json
当前 sidecar 需要的 hook point json / per-candidate output json
```

不要默认读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史 rounds 下的完整大文件
.codex-skills/**
```

## 5. Required Audit

Codex 执行前必须在 report 中记录：

```text
1. 确认 decision_id=decision_20260525_reverse_arg0_bounded_writer_rerun。
2. 确认 mainline=reverse_solving，skill_profiles 为 reverse-agent-iteration@v2 与 samplereverse-frontier@v2。
3. 确认 task_packet.task / derived_task 只是派生建议，当前执行权威是 decision_packet.md。
4. 确认 compare_real_lhs_provenance_audit freshness=current，source_run=sr_lhs_hook_observation_reliability_20260524_r4。
5. 确认上一轮 sidecar 已支持 arg0_final_data_writer_trace_point。
6. 确认当前 blocker 是 arg0_final_writer_trace_schema_gap。
7. 确认本轮只运行固定 candidates 的 bounded sidecar rerun。
8. 确认没有 Base64/RC4 probe、old solver、candidate search、beam/budget/timeout/frontier 扩张。
```

运行后必须在 report 中记录：

```text
1. 新 run-name。
2. 实际命令。
3. 固定 candidates 列表。
4. 每个 candidate 的 0x253a / 0x2559 / 0x258b / 0x258c row 是否观测到。
5. 每个 candidate 的 actual_arg0、pre_push_esi、reload_value、slot_writer_value 是否一致。
6. write ring raw_write_count、intersecting_write_count、nearest_write、final writer status。
7. 是否生成新 artifact，以及是否写入 artifact_index.latest_artifacts_v2。
8. 新 current_bottleneck.blocker。
```

## 6. Implementation Scope

### Phase A：preflight only-read check

先做只读检查，不改代码：

```text
1. 读取 current_state / artifact_index。
2. 确认上一轮 `arg0_final_data_writer_trace_point` 字段已存在于 sidecar。
3. 确认 strategy/project_state 已能聚合 `arg0_final_data_writer_trace`。
4. 确认 selected candidates 为 current actual compare evidence 中的三个固定 candidate。
```

如果 sidecar/schema 缺失上一轮字段，停止并报告 `arg0_writer_trace_runtime_blocked`，不要临时扩大任务范围重写架构。

### Phase B：一次 bounded sidecar rerun

执行一次新的 bounded run，run-name 固定为：

```text
sr_arg0_bounded_writer_trace_20260525_r1
```

本轮只允许采集以下 hook points：

```text
module+0x253a old_lhs_slot_store / slot writer before [ebp-0x1170]
module+0x2559 post_handoff_lhs_reload / reload source into ESI
module+0x258b pre_compare_push_esi / push ESI before compare arg0
module+0x258c static_compare_callsite / actual compare callsite
```

运行限制：

```text
只使用 current samplereverse sample。
只使用 current fixed candidates：
- 78d540b49c59077041414141414141
- 5a3e7f46ddd474d041414141414141
- 78d540b49c59076f41414141414141
不得增加 candidate。
不得扩大 timeout/budget/beam/topN/frontier。
不得触发 Base64/RC4 probe。
不得提交完整 solve_reports。
```

如果 Codex 无法确定现有 harness 命令，应优先检查现有 strategy/harness 调用方式；仍无法确定时，执行最小 sidecar direct command，并在 report 中写清楚环境阻断或命令缺口。不要回到旧 solver。

### Phase C：aggregation and projection

rerun 后必须执行 project_state build：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1
```

目标：让 `artifact_index.latest_artifacts_v2` 指向新 run 的 current artifacts，并让 `current_state.latest_compare_real_lhs_provenance_audit.arg0_final_data_writer_trace` 反映新 runtime evidence。

允许对以下文件做最小修补：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

仅当新 artifact 字段格式与上一轮预期不一致时才允许修补。禁止重构 harness、skill、registry 或工程支线。

分类规则：

```text
arg0_final_data_writer_identified:
- 有 runtime-backed data write；
- write range intersects actual_arg0 compare window；
- candidate relation 清楚；
- pointer carrier / pointer write / final data writer 区分清楚。

arg0_pointer_chain_identified_writer_missing:
- 0x253a/0x2559/0x258b/0x258c 指针链被 runtime-backed 观测；
- 但没有 data write intersect actual_arg0。

arg0_final_writer_not_observed_in_bounded_window:
- 0x258c actual compare 被观测；
- bounded window 内没有足够 writer 事件。

arg0_writer_trace_runtime_blocked:
- sidecar 或 environment 阻断，不能形成可信 runtime row。

arg0_final_writer_trace_schema_gap:
- 新 run 仍缺必要字段，无法区分 pointer write 与 data write。
```

### Phase D：report and archive

必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
```

建议归档时包含 diff：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260525_reverse_arg0_bounded_writer_rerun --include-diff
```

如果工具不支持 `--include-diff`，则使用默认 archive，并在 report 中明确 `included_diff=false` 的限制。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or pointer or writer or raw_write or provenance or classification"
python -m pytest -q tests/test_project_state.py -k "artifact or provenance or bottleneck or decision or report or pointer or writer"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果 sidecar/harness runtime 失败，仍必须运行可运行的 py_compile、focused tests、lint-decision、status、lint-report，并在 pytest_result 中记录失败命令和环境原因。

不需要运行：

```text
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
2. current_state 与 artifact_index 的 selected run 冲突，且无法解释。
3. 新 sidecar rerun 必须扩大 candidate set、timeout、budget、beam、topN 或 frontier 才能继续。
4. 必须运行 Base64/RC4 probe 或 old solver 才能继续。
5. 必须读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 不能区分 pointer carrier、pointer write、final data writer。
7. 新 run artifact 没有必要字段，且无法通过最小修补保留兼容。
8. 只能得到 pointer write，却需要声明 final_writer_identified。
9. 需要修改 .codex-skills 或 registry 才能继续。
10. 测试无法运行且没有记录环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260525_reverse_arg0_bounded_writer_rerun",
  "round_id": "round_20260525_reverse_arg0_bounded_writer_rerun",
  "based_on_decision_id": "decision_20260525_reverse_arg0_bounded_writer_rerun",
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
1. current artifact freshness/source_run 检查。
2. 新 run-name 与执行命令。
3. fixed candidates 列表。
4. 0x253a / 0x2559 / 0x258b / 0x258c runtime row table。
5. pointer carrier、pointer write、final data writer 的区分结论。
6. write ring summary：raw_write_count、intersecting_write_count、nearest_write、final_writer_status。
7. 新 current_bottleneck.blocker。
8. 是否生成新 artifact。
9. 真实测试命令和结果。
10. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- 新 bounded sidecar rerun 完成；
- 新 artifact freshness=current；
- actual arg0 final data writer 被 runtime-backed 证据解释，且 write range intersects actual_arg0 compare window；
- pointer carrier / pointer write / final data writer 严格区分；
- 未运行禁止 probe，未扩大搜索；
- tests/lints 通过。

ACCEPTED_WITH_LIMITATIONS：
- 新 bounded sidecar rerun 完成；
- 0x253a/0x2559/0x258b/0x258c 指针链被 runtime-backed 观测；
- final data writer 仍未确认，但 gap classification 更具体。

REWORK_REQUIRED：
- 没有运行 bounded sidecar rerun，却没有环境阻断说明；
- 把 pointer carrier 或 pointer write 伪称 final data writer；
- 把 stale artifact 当 current evidence；
- 运行 Base64/RC4 probe、old solver 或扩大搜索；
- report/decision/pytest id mismatch。

BLOCKED：
- runtime 环境阻断；
- current artifact 缺失且无法 rebuild；
- 必要测试无法运行；
- 新 sidecar artifact schema 无法被聚合。
```

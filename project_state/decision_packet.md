```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260524_reverse_lhs_writer_classification_trace",
  "round_id": "round_20260524_reverse_lhs_writer_classification_trace",
  "based_on_state_build_id": "state_20260524_042629_10b992a9fad9",
  "based_on_state_digest": "10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮回到**逆向解题主线**，不是工程架构改造支线。Phase 2 skill-centered handoff 已经 closeout；本轮不要继续扩张 skill、registry、sync 或 agent runtime。

当前 `task_packet.task` / `derived_task` 为 `Improve compare lhs last-writer instrumentation`，但本轮执行权威仍以本 `project_state/decision_packet.md` 为准。`task_packet.execution_scope = decision_packet_controls_current_round`。

本轮聚焦当前逆向瓶颈：

```text
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.stage = compare_real_lhs_provenance_audit
```

目标不是扩大搜索，也不是跑 Base64/RC4 probe；目标是追清当前 `compare_real_lhs_provenance_audit` / sidecar / aggregation 之间的证据链：为什么当前证据还没有形成 runtime-backed compare arg0 LHS writer 结论。

## 1. Goal

本轮目标：

```text
1. 从 project_state/artifact_index.json 的 latest_artifacts_v2 出发，定位当前 freshness=current 的 compare_real_lhs_provenance_audit artifact。
2. 有界读取该 artifact，记录真实 counters 与分类：classification、runtime_backed_count、lhs_side/flag_side、write_monitor_health、last_writer_summary、missing_candidate_reasons、last_writer_candidates。
3. 审计 sidecar 输出字段到 compare_aware_search 聚合字段的路径，确认 writer evidence 是否在以下任一环节丢失：
   - Olly sidecar event / write monitor 输出；
   - harness artifact JSON；
   - compare_aware_search 解析 / 聚合；
   - current_state / task_packet 派生；
   - final classification / blocker reason。
4. 如果当前 artifact 已经存在 raw/retained/intersecting writer evidence，但最终仍分类为 writer missing，则修复最小的聚合或分类逻辑，并补单元测试。
5. 如果当前 artifact 明确显示 raw_write_count=0 或 filtered_intersecting_write_count=0，则不要伪造 writer；只补齐可审计 blocker 诊断，让 report 明确停在 write-monitor observation gap，而不是误称已有 runtime-backed writer。
6. 保持 bounded：优先静态代码审计、artifact 有界读取和单元测试。只有在代码改动后确有必要验证 artifact schema 时，才允许一次 bounded harness rerun，并必须使用新的 run-name，不得扩大 candidate/search/budget。
```

本轮不求最终 flag，不做 candidate search，不扩大 frontier。

## 2. Current Evidence

当前任务主线：**逆向解题主线**。

当前状态：

```text
state_build_id = state_20260524_042629_10b992a9fad9
based_on_state_digest = 10b992a9fad9e13c9c445709a1f2fb6cee05ed8450b451e0b3d2c80226af04fd
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.stage = compare_real_lhs_provenance_audit
```

`artifact_index.latest_artifacts_v2` 已有 freshness 语义。当前 run 指向：

```text
latest_harness_run / selected run = sr_lhs_hook_observation_reliability_20260524_r4
```

但 artifact_index 中仍有大量 legacy/stale/missing artifact，因此本轮不能把旧 `solve_reports/tool_artifacts/*` 或旧 harness run 当作 current 证据。必须优先以 `latest_artifacts_v2` 中 freshness=current 的 artifact 为准。

当前 `current_state` 仍包含旧函数语义和已知 transform 信息：

```text
known_transform = input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
0x401b50 = candidate_dependent, hookable, instruction_confirmed, semantic_guess=copy_or_handoff
```

但旧 archived round `round_20260523_samplereverse_lhs_last_writer_instrumentation` 显示曾出现 `instrumentation_incomplete`，例如 write monitor enabled 但 raw/intersecting writes 为 0。该旧报告只能作为历史背景，不能覆盖当前 selected run 的 artifact。当前 Codex 必须重新读取当前 artifact 并报告真实 counters。

Phase 2 工程支线已完成并 closeout，skill 只承载长期流程规范；动态样本事实必须继续保留在 `project_state/current_state.json`、`artifact_index.json`、`negative_results.json`，不得写回 `.codex-skills`。

## 3. Do Not Do

不要做以下事情：

```text
不要继续 Phase 2 工程支线改造。
不要修改 .codex-skills/、tools/sync_codex_skills.ps1、tools/audit_codex_skills.py，除非只是被测试读取。
不要推进通用 agent runtime、远程 skill 下载、registry 扩张。
不要回 old sample_solver blind search。
不要扩大 beam / topN / budget / timeout / frontier iteration。
不要运行 Base64/RC4 breakpoint probe。
不要运行 Base64/RC4 probe 的任何变体，除非新 decision 明确批准。
不要把 compare_semantics_agree=false candidates 作为 primary frontier。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要默认读取 PROJECT_PROGRESS_LOG.txt。
不要复用旧 [ebp-0x1170] 作为真实 LHS 来源，除非当前 artifact 提供 runtime-backed provenance。
不要把 stale/missing artifact 当 current evidence。
不要把 compare_probe fallback args 当 writer provenance；fallback 只可证明 actual compare arg0/arg1，不可证明 writer。
不要为了“看起来有进展”伪造 runtime-backed writer 结论。
```

同时遵守 `negative_results.json` 中已有禁止方向，尤其是：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
rerun Base64/RC4 breakpoint probe before real lhs producer identification
reuse old [ebp-0x1170] without real-lhs provenance evidence
run Base64/RC4 breakpoint probe before real lhs producer identification
```

## 4. Files To Inspect

必须检查：

```text
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取的 artifact：

```text
project_state/artifact_index.json 中 latest_artifacts_v2["compare_real_lhs_provenance_audit"] 指向的 path
```

如 artifact_index 指向 current run，还可有界读取：

```text
solve_reports/harness_runs/<selected_run>/summary.json
solve_reports/harness_runs/<selected_run>/run_manifest.json
```

仅在 artifact_index 缺失、freshness 不可信或 current artifact 不存在时，才运行：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_hook_observation_reliability_20260524_r4
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
.codex-skills/**
tools/sync_codex_skills.ps1
```

## 5. Required Audit

Codex 修改前必须完成并在报告中记录：

```text
1. 读取本 decision_meta，确认 decision_id = decision_20260524_reverse_lhs_writer_classification_trace，status=APPROVED，mainline=reverse_solving，skill_profiles 包含 reverse-agent-iteration@v2 和 samplereverse-frontier@v2。
2. 读取 task_packet，确认 task/derived_task 是样本派生任务，但 execution_scope 表明当前执行权威来自 decision_packet.md。
3. 读取 current_state，确认 current_bottleneck.reason=compare_lhs_runtime_backed_writer_missing。
4. 读取 artifact_index.latest_artifacts_v2，确认 compare_real_lhs_provenance_audit 的 path、source_run、freshness。
5. 读取该 current artifact，记录 classification、runtime_backed_count、lhs_side、flag_side、write_monitor_health、last_writer_summary、last_writer_candidates、missing_candidate_reasons。
6. 读取 negative_results，确认本轮不会触发 old sample_solver、Base64/RC4 probe、beam/budget 扩张、完整 solve_reports commit。
7. 审计 compare_pre_compare_handoff_target_probe.py 中 write monitor / write ring / hook observation 输出字段。
8. 审计 compare_aware_search.py 中 artifact 解析、last_writer_summary 聚合、missing_candidate_reasons、sidecar_harness_status / activity_compare classification 逻辑。
9. 明确判断当前 blocker 属于以下哪类：
   - artifact_missing_or_stale；
   - no_raw_write_events_observed；
   - raw_writes_not_intersecting_arg0；
   - intersecting_writer_present_but_dropped_by_aggregation；
   - intersecting_writer_present_but_final_classification_not_promoted；
   - schema_mismatch_between_sidecar_and_aggregator。
10. 报告中必须说明是否运行 harness；默认不运行。
```

## 6. Implementation Scope

### Phase A：Current artifact evidence audit

先做只读证据审计，不要直接改代码。

输出到 `codex_execution_report.md` 的 evidence table 至少包含：

```text
artifact_path
source_run
freshness
classification
runtime_backed_count
lhs_side / flag_side
write_monitor_health.enabled
write_monitor_health.raw_write_count
write_monitor_health.filtered_intersecting_write_count
last_writer_summary.raw_write_event_count
last_writer_summary.retained_write_count
last_writer_candidates count
missing_candidate_reasons summary
```

如果 artifact 不存在或 freshness 不是 current，停止并转为 `BLOCKED` 或先运行 bounded project_state build；不要基于 stale artifact 写代码结论。

### Phase B：Classification path trace

建立一张从 sidecar 到 final classification 的字段映射表：

```text
sidecar output field -> artifact JSON field -> compare_aware_search parsed field -> current_state/task_packet field -> final classification / status
```

目标是定位 writer evidence 丢失点，而不是新增大功能。

### Phase C：Minimal fix if evidence is dropped

仅当 Required Audit 证明当前 artifact 中已经有 intersecting writer evidence，但聚合/分类没有消费时，允许修改：

```text
reverse_agent/strategies/compare_aware_search.py
```

可能的最小修复：

```text
1. 修复字段名不一致。
2. 修复 retained/intersecting writer 过滤条件。
3. 修复 sidecar_harness_status / activity_compare classification promotion。
4. 增加 lhs_writer_classification_blocker 字段，明确卡点。
```

必须补测试，不能只改逻辑。

### Phase D：Minimal sidecar diagnostic if evidence is absent

仅当当前 artifact 明确没有 raw/intersecting writer evidence，且代码审计发现 sidecar 输出缺少足够诊断时，允许小幅修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
```

限制：

```text
只增加诊断字段或 schema 稳定化；不要改 hook 范围，不要扩 runtime probe，不要扩大 candidate set。
```

### Phase E：Tests

至少补或更新单元测试覆盖当前判断：

```text
1. artifact has raw/intersecting writer -> aggregator retains writer and status reflects writer evidence。
2. artifact has raw_write_count=0 -> status remains missing/incomplete but blocker reason is explicit。
3. compare_probe fallback establishes compare args but not writer provenance。
4. stale/missing artifact must not be treated as current writer evidence。
```

### Phase F：Project state/report

本轮结束必须写入：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果代码改动会影响 project_state 派生，运行：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如果运行新 harness，必须使用新的 bounded run-name，例如：

```text
sr_lhs_writer_classification_trace_20260524_r1
```

但默认不要运行 harness；只有当单元测试无法验证 artifact schema / classification path 时才允许。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "last_writer or real_lhs or provenance or classification"
python -m pytest -q tests/test_project_state.py -k "artifact or provenance or decision or report"
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 project_state 派生逻辑或重新 build project_state，必须补充：

```bash
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

如运行 harness，必须记录完整命令，并满足：

```text
只运行当前 sample / current fixed candidates / current strategy。
不得扩大 search budget / beam / topN / timeout。
不得运行 Base64/RC4 probe。
```

不需要运行：

```bash
full pytest unrelated suites
full solve_reports scan
PROJECT_PROGRESS_LOG read
Base64/RC4 breakpoint probe
old sample_solver
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. artifact_index.latest_artifacts_v2 缺失或 compare_real_lhs_provenance_audit freshness 不是 current，且不能有界 rebuild project_state。
2. current artifact 路径不存在。
3. 当前 artifact 与 current_state 的 current_bottleneck 明显冲突，且无法解释。
4. 需要读取完整 solve_reports 才能定位证据。
5. 需要读取完整 PROJECT_PROGRESS_LOG 才能定位证据。
6. 需要运行 Base64/RC4 probe、old sample_solver、beam/budget 扩张才能继续。
7. 需要新增大范围 runtime hooks 才能继续。
8. 需要修改 .codex-skills 或 sync/audit 工具才能继续。
9. 不能区分 compare arg fallback 与 writer provenance。
10. 代码改动会把 stale/missing artifact 当 current evidence。
11. 测试无法运行且没有合理环境原因。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260524_reverse_lhs_writer_classification_trace",
  "round_id": "round_20260524_reverse_lhs_writer_classification_trace",
  "based_on_decision_id": "decision_20260524_reverse_lhs_writer_classification_trace",
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
1. 当前 artifact path/source_run/freshness。
2. 当前 artifact counters 与 classification。
3. writer evidence 是否存在。
4. 如果存在，在哪一层被丢弃或未提升。
5. 如果不存在，明确 blocker reason。
6. 是否修改 compare_aware_search.py / sidecar。
7. 是否运行 harness；默认应为 no。
8. 真实测试命令和结果。
9. 是否运行 archive-round；如果未运行，说明原因。
10. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- 当前 artifact freshness 被正确核验。
- writer evidence path 被清楚追踪。
- 如果 evidence 存在但聚合丢弃，已最小修复并测试。
- 如果 evidence 不存在，已明确 blocker reason，未伪造 writer。
- 未运行禁止 probe，未扩大 search。
- tests 通过。

ACCEPTED_WITH_LIMITATIONS：
- 完成 artifact/分类路径审计，但由于 current artifact 缺少 writer evidence，只能补 blocker 诊断。
- 未运行 harness，但单元测试和报告足以定位下一步。

REWORK_REQUIRED：
- 把 stale artifact 当 current evidence。
- 把 compare_probe fallback 当 writer provenance。
- 未读取 current artifact 就修改分类逻辑。
- 运行 Base64/RC4 probe 或 old sample_solver。
- 扩大 beam/budget/topN。
- codex_report_summary.based_on_decision_id 不匹配。

BLOCKED：
- current artifact 缺失且无法 rebuild。
- project_state 与 artifact_index 严重冲突。
- 无法运行必要测试。
```

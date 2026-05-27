```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260526_validate_hook_readiness_ordering",
  "round_id": "round_20260526_validate_hook_readiness_ordering",
  "based_on_state_build_id": "state_20260526_142759_b67381ec8490",
  "based_on_state_digest": "b67381ec8490e43797eef345662a874256e77c116b6081104672a6d7e8d024f6",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **reverse_solving** 主线。目标不是搜索 candidate，也不是继续做泛化诊断；目标是基于上一轮已经收敛出的具体 blocker：

```text
hooks_not_ready_before_ui_trigger
```

做一次最小、可审计的 hook-readiness ordering 修复与验证，使 UI trigger 只在 compare-real-LHS sidecar 确认 hooks installed / hooks ready 后发生，并用同一批 current candidates 做一次 bounded rerun 验证 observation delivery。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只作为派生建议，不自动覆盖本 decision。

本轮不得在执行过程中改写 `project_state/decision_packet.md` 本体；如需归档，只能写入 `project_state/rounds/<round_id>/decision_packet.md`。

## 1. Goal

修复或验证 `compare_real_lhs_provenance_audit` sidecar 的 hook-readiness ordering，使当前 blocker 从：

```text
hooks_not_ready_before_ui_trigger
```

推进到以下二者之一：

```text
1. observation delivery 成功：ui_trigger_after_hooks_installed=true，且 actual_compare.arg0/arg1 至少有 compare-arg observation。
2. 如果仍失败，给出比 hooks_not_ready_before_ui_trigger 更具体的新 blocker，例如：
   - ui_trigger_executed_but_compare_arg_observation_missing
   - message_bridge_dropped_observation
   - hook_installed_but_compare_call_not_reached_in_same_process
   - compare_arg_payload_schema_gap
   - sidecar_runtime_precondition_failed
```

必须完成：

```text
1. 定位 compare_real_lhs_provenance sidecar / script template 中 UI trigger 与 hook installation 的顺序。
2. 确认上一轮 artifact 中 ui_trigger_after_hooks_installed=false 的成因。
3. 如果当前代码缺少 hooks-ready barrier，做最小修复：UI trigger 必须等待 hooks_installed 或 hooks_ready_barrier。
4. 如果代码已有 barrier，解释为什么仍然 false，并修复等待条件、状态传播或 telemetry projection。
5. 只使用当前 3 个 candidates 做一次 bounded rerun 验证，不扩大 search、timeout、budget、beam、topN。
6. 重新 build project_state，使新 run 的 compare_real_lhs_provenance_audit 在 latest_artifacts_v2 中标记为 current。
7. 更新 codex_execution_report.md 和 pytest_result.txt，报告必须包含 rerun command、run_name、artifact path、classification、tests。
```

本轮完成标准不是解出 flag，而是打通或进一步定位 compare arg observation delivery。

## 2. Current Evidence

当前主线：

```text
mainline = reverse_solving
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_mainline = L15(prefix8)
```

当前 state：

```text
state_build_id = state_20260526_142759_b67381ec8490
state_digest = b67381ec8490e43797eef345662a874256e77c116b6081104672a6d7e8d024f6
source_run = sr_arg0_bounded_writer_trace_20260525_r1
```

当前 bottleneck：

```text
stage = compare_real_lhs_provenance_audit
reason = inconclusive
blocker = hooks_not_ready_before_ui_trigger
confidence = medium
```

上一轮已接受但有限制：

```text
review_conclusion = ACCEPTED_WITH_LIMITATIONS
core_result = blocker narrowed from arg0_ui_trigger_or_timeout_blocked to hooks_not_ready_before_ui_trigger
limitation_1 = pytest_result summary listed status/lint-report/git diff --check but body did not expand them
limitation_2 = prior execution modified decision_packet.md; this round must not do that again
```

当前 relevant current artifact：

```text
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.compare_real_lhs_provenance_audit.path = solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

当前 artifact 中已知 telemetry：

```text
hook_install_status = installed
hook_count/requested_hook_count = 4/4
script_load_status = loaded
python_message_callback_registered_before_load = true
python_message_count_total = 116, 22, 23
frida_message_error_count = 0
python_message_decode_error_count = 0
ui_trigger_status = button_triggered
ui_trigger_after_hooks_installed = false
observation_count = 0
post_ui_observation_count = 0
```

当前 compare symptom：

```text
actual_compare.entry = 0x258c
actual_compare.entry_status = confirmed
actual_compare.observed_count = 3
actual_compare.arg0_value_by_candidate = {}
actual_compare.arg0_preview_by_candidate = {}
actual_compare.arg1_value_by_candidate = {}
actual_compare.arg1_preview_by_candidate = {}
sidecar_observation_blocker = hooks_not_ready_before_ui_trigger
lhs_writer_classification_blocker = hooks_not_ready_before_ui_trigger
```

当前 bounded candidate set 只能使用：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

`task_packet.task` / `derived_task` 仍只是状态派生建议；本文件控制当前轮任务。

## 3. Do Not Do

严禁：

```text
1. 不运行 Base64/RC4 breakpoint probe。
2. 不回退旧 sample_solver 盲搜。
3. 不扩大 beam / topN / budget / timeout / frontier iteration。
4. 不启动新的 candidate search。
5. 不追 final writer。
6. 不把 stale compare_probe / stale handoff artifacts 当 current evidence。
7. 不读取完整 solve_reports/。
8. 不读取完整 PROJECT_PROGRESS_LOG.txt。
9. 不提交完整 solve_reports/。
10. 不修改 .codex-skills/、registry、sync 或 agent runtime。
11. 不把动态 runtime facts 写入 .codex-skills/。
12. 不通过删除测试、降低断言或绕过 classification 来制造通过。
13. 不在执行中改写 project_state/decision_packet.md 本体。
14. 不重复 negative_results 中的失败方向，包括 exact2 basin value-pool、H1/H3 fixed contrast set、旧 transform trace consistency、旧 producer material confirmation、Base64/RC4 material producer 假设。
```

特别限制：

```text
本轮可以运行一次 bounded rerun，但它不是搜索；它只能验证 hook-readiness ordering。
本轮可以新增一个 run，例如 sr_arg0_hook_readiness_ordering_20260526_r1。
本轮不得扩大 current candidates，不得调大 timeout/budget。
```

## 4. Files To Inspect

默认必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

代码必须检查：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/sidecar_health.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界检查当前 artifact：

```text
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\summary.json
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\run_manifest.json
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

必要时检查 sidecar script/template：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/*compare*lhs*
compare_aware_search.py 中实际生成 compare_real_lhs_provenance sidecar 的代码段
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史所有 rounds/
```

## 5. Required Audit

Codex 报告必须回答：

```text
1. UI trigger 在当前 sidecar 中发生于 hooks_installed 之前、之后，还是状态记录错误。
2. 是否存在明确的 hooks-ready barrier；如果有，为什么上一轮 ui_trigger_after_hooks_installed=false。
3. 修复点属于：sidecar wait condition、script lifecycle event、message bridge、aggregation、project_state projection，还是 runtime environment precondition。
4. bounded rerun 是否只用了当前 3 个 candidates。
5. bounded rerun 后：
   - hook_install_status
   - hook_count/requested_hook_count
   - hooks_ready_before_ui_trigger
   - ui_trigger_after_hooks_installed
   - ui_trigger_status
   - observation_count
   - post_ui_observation_count
   - actual_compare.entry_status
   - actual_compare.arg0/arg1 maps
   这些字段分别是什么。
6. 如果 compare arg 仍为空，新的 blocker 必须比 hooks_not_ready_before_ui_trigger 更具体。
7. 是否有 stale/missing artifact 被错误当成 current；必须明确说明没有。
8. 是否遵守 negative_results；必须明确说明没有重复禁止方向。
9. pytest_result.txt 正文必须展开 status、lint-report、git diff --check 的结果，不能只写在 summary。
10. 本轮不得改写 project_state/decision_packet.md；报告必须声明是否遵守。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260526_validate_hook_readiness_ordering",
  "round_id": "round_20260526_validate_hook_readiness_ordering",
  "based_on_decision_id": "decision_20260526_validate_hook_readiness_ordering",
  "status": "SUCCESS_OR_BLOCKED_OR_REWORK_REQUIRED",
  "acceptance_recommendation": "ACCEPTED_OR_ACCEPTED_WITH_LIMITATIONS_OR_REWORK_REQUIRED_OR_BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/sidecar_health.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

仅当确认 hook-readiness telemetry 或 UI trigger ordering 位于 script/template 时，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/*compare*lhs*
```

允许新增或更新的 project_state 输出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
project_state/model_gate.json
project_state/rounds/round_20260526_validate_hook_readiness_ordering/*
```

不得更新：

```text
project_state/decision_packet.md
.codex-skills/*
完整 solve_reports/*
PROJECT_PROGRESS_LOG.txt
```

允许生成的新 run 名建议：

```text
sr_arg0_hook_readiness_ordering_20260526_r1
```

bounded rerun 必须满足：

```text
1. candidate set exactly equals current 3 candidates。
2. 不扩大 timeout/budget/beam/topN。
3. 不运行 Base64/RC4 probe。
4. 不启动 search。
5. 只通过 project_state/artifact_index 引用新 artifact。
6. 不提交完整 solve_reports。
```

## 7. Tests

必须运行并在 `project_state/pytest_result.txt` 正文逐条记录结果：

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py reverse_agent/sidecar_health.py

python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or observation or sidecar or ui or trigger or timeout or lifecycle or classification or readiness"

python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime or projection or readiness"

python -m pytest -q tests/test_project_state.py

python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_run_name_if_rerun_else_sr_arg0_bounded_writer_trace_20260525_r1>

python -m reverse_agent.project_state lint-decision --state-dir project_state

python -m reverse_agent.project_state status --state-dir project_state

python -m reverse_agent.project_state lint-report --state-dir project_state

git diff --check
```

如果执行 bounded rerun，还必须记录：

```text
1. 实际 rerun command。
2. new_run_name。
3. 新 compare_real_lhs_provenance_audit path。
4. 新 artifact_index.latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness。
5. ui_trigger_after_hooks_installed 是否为 true。
6. actual_compare.arg0/arg1 是否捕获。
7. 如果未捕获，新 blocker 是什么。
```

如果无法安全执行 bounded rerun，必须停止并报告 `BLOCKED`，不能转向搜索或扩大预算。

## 8. Stop Conditions

遇到以下情况立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 需要读取完整 solve_reports/ 才能继续。
2. 需要 PROJECT_PROGRESS_LOG.txt 才能继续。
3. 需要 Base64/RC4 runtime probe 才能继续。
4. 需要扩大 candidate、beam、topN、timeout、budget 才能继续。
5. 无法限制 rerun 到当前 3 个 candidates。
6. current artifact 不是 current，或 source_run 无法解释。
7. hook-readiness 修复需要重构 agent runtime 或 skill 系统。
8. 修复只能靠删除测试、降低断言或绕过 classification。
9. bounded rerun 需要提交完整 solve_reports。
10. lint-decision / lint-report / pytest_result 元数据无法与本 decision_id 对齐。
11. 执行中需要修改 project_state/decision_packet.md 本体。
```

本轮成功标准：

```text
1. UI trigger ordering 被修复或被精确证明不是当前阻断点。
2. bounded rerun 只使用当前 3 个 candidates。
3. 新 project_state 指向新 current artifact，且 freshness 正确。
4. blocker 从 hooks_not_ready_before_ui_trigger 推进为 observation success 或更具体 blocker。
5. report / pytest_result / lint-report 元数据全部匹配。
6. 没有推进搜索、没有 Base64/RC4 probe、没有 final-writer chase。
```

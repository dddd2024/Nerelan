```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260527_diagnose_compare_arg_observation_missing",
  "round_id": "round_20260527_diagnose_compare_arg_observation_missing",
  "based_on_state_build_id": "state_20260527_084821_6904311ce1cc",
  "based_on_state_digest": "6904311ce1cc50bc324c75e2807dce7d08584c9d7e14469f736d8910477eeb77",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **reverse_solving** 主线。上一轮已经完成 hook-readiness ordering 修复：UI trigger 已经发生在 hooks ready 之后，旧 blocker `hooks_not_ready_before_ui_trigger` 不再是当前问题。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只作为状态派生建议，不自动覆盖本 decision。

本轮目标不是搜索 candidate，不是追 final writer，不是 Base64/RC4 probe，也不是重复 hook-readiness 修复；目标是围绕新 blocker：

```text
ui_trigger_executed_but_compare_arg_observation_missing
```

做一次最小、可审计的 observation-delivery 诊断，判断 compare-arg observation 缺失到底发生在 hook address / hook hit / JS payload / Python message bridge / aggregation / project_state projection 哪一层。

## 1. Goal

把当前 blocker 从：

```text
ui_trigger_executed_but_compare_arg_observation_missing
```

推进到以下结果之一：

```text
1. observation delivery 成功：actual compare hook 至少产生 compare-arg observation，actual_compare.arg0/arg1 maps 不再为空。
2. 如果仍失败，给出更具体的新 blocker，例如：
   - hook_installed_but_compare_call_not_reached_after_ui_trigger
   - static_compare_callsite_address_mismatch
   - hook_hit_payload_emitted_but_python_filter_dropped
   - python_message_bridge_received_but_aggregation_dropped
   - compare_arg_payload_schema_gap
   - ui_trigger_success_but_target_path_skipped_compare_call
   - sidecar_runtime_precondition_failed
```

必须完成：

```text
1. 有界读取 current compare_real_lhs_provenance_audit artifact，确认每个 candidate 的 hook install telemetry、hook address、ui trigger timing、message counts、observation counts、actual_compare fields。
2. 审计 sidecar 中 actual compare / static_compare_callsite hook 的命名、module_offset、Interceptor.attach 地址、send payload schema、Python message filter、aggregation projection。
3. 不重复上一轮 hook-readiness ordering 修复；仅在定位到 payload/filter/aggregation 缺口时做最小修复。
4. 如需 runtime 验证，只允许使用当前 3 个 candidates 做一次 bounded rerun，不扩大 search、timeout、budget、beam、topN。
5. 重新 build project_state，使新证据在 latest_artifacts_v2 中为 current。
6. 更新 codex_execution_report.md 和 pytest_result.txt，报告必须包含 run_name、artifact path、classification、new blocker、tests、lint-decision、lint-report、git diff --check。
```

本轮完成标准不是解出 flag，而是定位或打通 compare-arg observation delivery。

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
state_build_id = state_20260527_084821_6904311ce1cc
state_digest = 6904311ce1cc50bc324c75e2807dce7d08584c9d7e14469f736d8910477eeb77
source_run = sr_arg0_hook_readiness_ordering_20260526_r1
```

上一轮审计结论：

```text
review_conclusion = ACCEPTED_WITH_LIMITATIONS
accepted_core = hook-readiness ordering was fixed and bounded rerun advanced blocker
limitation = old decision_packet digest mismatch after project_state build; this new decision resolves that mismatch by binding to the rebuilt state
```

当前 bottleneck：

```text
stage = compare_real_lhs_provenance_audit
reason = instrumentation_incomplete
blocker = ui_trigger_executed_but_compare_arg_observation_missing
confidence = medium
```

当前 relevant current artifact：

```text
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_hook_readiness_ordering_20260526_r1
latest_artifacts_v2.compare_real_lhs_provenance_audit.path = solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

上一轮 rerun telemetry 摘要：

```text
classification = instrumentation_incomplete
sidecar_observation_blocker = ui_trigger_executed_but_compare_arg_observation_missing
lhs_writer_classification_blocker = ui_trigger_executed_but_compare_arg_observation_missing
hook_install_status = installed for all 3 candidates
hook_count/requested_hook_count = 4/4 for all 3 candidates
hooks_ready_barrier_seen = true for all 3 candidates
hooks_ready_before_ui_trigger = true for all 3 candidates
ui_trigger_after_hooks_installed = true for all 3 candidates
ui_trigger_status = button_triggered for all 3 candidates
ui_trigger_timing_status = hooks_ready_before_ui_trigger for all 3 candidates
observation_count = 0 for all 3 candidates
post_ui_observation_count = 0 for all 3 candidates
actual_compare.entry_status = confirmed
actual_compare.arg0/arg1 maps = empty
```

当前 bounded candidate set 只能使用：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前 skill profiles 来自 active registry：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

`task_packet.task` / `derived_task` 是 `Diagnose sidecar observation delivery blocker`，但仍只是状态派生建议；本文件控制当前轮任务。

## 3. Do Not Do

严禁：

```text
1. 不运行 Base64/RC4 breakpoint probe。
2. 不回退旧 sample_solver 盲搜。
3. 不扩大 beam / topN / budget / timeout / frontier iteration。
4. 不启动新的 candidate search。
5. 不追 final writer。
6. 不重复上一轮 hook-readiness ordering 修复。
7. 不把 stale compare_probe / stale handoff artifacts 当 current evidence。
8. 不读取完整 solve_reports/。
9. 不读取完整 PROJECT_PROGRESS_LOG.txt。
10. 不提交完整 solve_reports/。
11. 不修改 .codex-skills/、registry、sync 或 agent runtime。
12. 不把动态 runtime facts 写入 .codex-skills/。
13. 不通过删除测试、降低断言或绕过 classification 来制造通过。
14. 不重复 negative_results 中的失败方向，包括 exact2 basin value-pool、H1/H3 fixed contrast set、旧 transform trace consistency、旧 producer material confirmation、Base64/RC4 material producer 假设、旧 [ebp-0x1170] 假设。
```

特别限制：

```text
本轮可以运行一次 bounded rerun，但它不是搜索；它只能验证 observation delivery diagnosis。
本轮不得扩大 current candidates，不得调大 timeout/budget。
本轮不得把 compare_probe fallback 提升为 provenance。
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
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/sidecar_health.py
reverse_agent/project_state.py
reverse_agent/strategies/compare_aware_search.py
tests/test_project_state.py
tests/test_compare_aware_search_strategy.py
```

必须有界检查当前 artifact：

```text
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\summary.json
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\run_manifest.json
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

必要时只检查当前 artifact 下的 per-candidate JSON，不要扫描完整 solve_reports：

```text
solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\candidate_*\compare_real_lhs_provenance_audit.json
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
1. actual compare / static_compare_callsite hook 的 module_offset 与 artifact 中 actual_compare.entry 是否一致。
2. Interceptor.attach 是否确认 installed，并且 hook_address_validation 是否 resolved。
3. UI trigger 后目标进程是否仍存活，是否有窗口/按钮触发成功证据。
4. JS 是否发送过任何 compare_pre_compare_handoff_target_observation payload。
5. 如果 JS 发送过 observation，Python on_message 是否收到；如果收到，aggregation 为什么没有投影到 actual_compare.arg0/arg1 maps。
6. 如果 JS 没有发送 observation，判断更具体原因是 compare call 未到达、hook 地址错、进程路径跳过 compare、还是 runtime precondition。
7. 新 blocker 必须比 ui_trigger_executed_but_compare_arg_observation_missing 更具体，除非 observation delivery 已成功。
8. 是否只使用当前 3 个 candidates；必须列出 candidate set。
9. 是否有 stale/missing artifact 被错误当成 current；必须明确说明没有。
10. 是否遵守 negative_results；必须明确说明没有重复禁止方向。
11. pytest_result.txt 正文必须展开 lint-decision、lint-report、git diff --check 的结果，不能只写在 summary。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260527_diagnose_compare_arg_observation_missing",
  "round_id": "round_20260527_diagnose_compare_arg_observation_missing",
  "based_on_decision_id": "decision_20260527_diagnose_compare_arg_observation_missing",
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
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/sidecar_health.py
reverse_agent/project_state.py
reverse_agent/strategies/compare_aware_search.py
tests/test_project_state.py
tests/test_compare_aware_search_strategy.py
```

允许新增或更新的 project_state 输出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
project_state/model_gate.json
project_state/rounds/round_20260527_diagnose_compare_arg_observation_missing/*
```

不允许修改：

```text
.codex-skills/*
PROJECT_PROGRESS_LOG.txt
完整 solve_reports/*
```

关于 `project_state/decision_packet.md`：

```text
本轮执行过程中原则上不得改写本 decision_packet。
如 project_state build 后 digest 再次变化，Codex 必须在 report 中声明 lint-decision mismatch，而不是自行覆盖 decision_packet。
```

## 7. Tests

至少运行并记录：

```text
python -m py_compile reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py reverse_agent/sidecar_health.py reverse_agent/strategies/compare_aware_search.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or observation or sidecar or ui or trigger or timing or classification or readiness or payload"
python -m pytest -q tests/test_project_state.py -k "sidecar or observation or blocker or report or runtime or projection or payload"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_or_current_run_name>
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果实际做了 bounded rerun，必须记录完整 rerun command、run_name、artifact path 和 candidate set。

如果没有做 rerun，必须说明为什么仅靠 artifact/code audit 已足够给出更具体 blocker。

## 8. Stop Conditions

立即停止并写 report，如果出现任一情况：

```text
1. 已成功获得 compare-arg observation，actual_compare.arg0/arg1 maps 不再为空。
2. 已定位到更具体 blocker，并有 artifact/code evidence 支撑。
3. runtime 环境无法启动 Frida/pywinauto/target，记录 sidecar_runtime_precondition_failed。
4. 需要扩大 candidate/search/timeout/budget 才能继续，此时不得扩大，必须停止并报告 BLOCKED。
5. 发现关键 artifact missing 或 freshness 非 current，先停止并要求有界重建 project_state。
6. 发现继续推进会重复 negative_results 禁止方向，立即停止。
```

本轮输出必须让下一轮 GPT 能直接判断：compare-arg observation 缺失是 hook 未命中、payload 未发送、bridge 未接收、aggregation 未投影，还是 target path 没有执行 compare call。

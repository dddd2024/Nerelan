```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260527_diagnose_compare_hook_path_not_reached",
  "round_id": "round_20260527_diagnose_compare_hook_path_not_reached",
  "based_on_state_build_id": "state_20260527_135835_189861793d69",
  "based_on_state_digest": "189861793d69622a050663bd67ce33dd1a04e8f62ec193d0a4ba1b21d3d9c9b6",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **reverse_solving** 主线。上一轮已经完成 observation-delivery 诊断：compare hook installation、hook address resolution、UI trigger、Python message bridge 均不是当前主要问题；当前 blocker 已推进为：

```text
hook_installed_but_compare_call_not_reached_after_ui_trigger
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只作为状态派生建议，不自动覆盖本 decision。

本轮目标不是搜索 candidate，不是追 final writer，不是 Base64/RC4 probe，不是再次诊断 message bridge / aggregation / project_state projection；目标是解释 **UI trigger 后为什么没有到达已安装的 static compare hook / compare-side hooks**。

## 1. Goal

把当前 blocker 从：

```text
hook_installed_but_compare_call_not_reached_after_ui_trigger
```

推进到以下结果之一：

```text
1. 证明 UI trigger 后确实到达 compare-side path，并获得至少一个 compare-side hook hit / observation。
2. 如果仍未到达，给出更具体的新 blocker，例如：
   - ui_button_triggered_but_decrypt_handler_not_entered
   - decrypt_handler_entered_but_candidate_path_exits_before_handoff
   - handoff_helper_not_entered_after_ui_trigger
   - handoff_helper_entered_but_return_path_skips_compare_window
   - static_compare_hook_address_stale_for_current_binary
   - ui_action_targets_wrong_process_or_window
   - target_path_requires_different_control_event
   - sidecar_runtime_precondition_failed
```

必须完成：

```text
1. 有界读取 current compare_real_lhs_provenance_audit artifact，确认已有证据：hooks installed/resolved、UI triggered、message bridge alive、observation_count=0、hook_hit_counts empty/zero。
2. 审计 current sidecar 的 hook point set，确认 static_compare_callsite 0x258c、pre_compare_lhs_push 0x258b、post_handoff_lhs_reload 0x2559、old_lhs_slot_store 0x253a 是否仍对应当前 patched binary 的 instruction boundary。
3. 设计一个最小 path-reachability audit：只围绕 UI trigger 后的 decrypt handler / handoff helper / pre-compare window 是否进入，不采集 final writer，不扩大 candidate set。
4. 如需要 runtime 验证，只允许使用当前 3 个 candidates 做一次 bounded rerun；不得扩大 search、timeout、budget、beam、topN。
5. 如果新增 artifact，必须命名清楚，例如 `compare_hook_path_reachability_audit.json` 或等价名称，并写入 artifact_index/latest_artifacts_v2 provenance/freshness。
6. 重新 build project_state，使新证据在 latest_artifacts_v2 中为 current。
7. 更新 codex_execution_report.md 和 pytest_result.txt，报告必须包含 run_name、artifact path、candidate set、classification、new blocker、tests、lint-decision、lint-report、git diff --check。
```

本轮完成标准不是解出 flag，而是回答：UI trigger 后路径没有命中 compare hook，是 UI/handler 没进、handler 早退、handoff 未进、handoff 返回路径跳过 compare、hook 地址 stale，还是 runtime precondition 问题。

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
state_build_id = state_20260527_135835_189861793d69
state_digest = 189861793d69622a050663bd67ce33dd1a04e8f62ec193d0a4ba1b21d3d9c9b6
source_run = sr_arg0_hook_readiness_ordering_20260526_r1
```

上一轮审计结论：

```text
review_conclusion = ACCEPTED_WITH_LIMITATIONS
accepted_core = observation-delivery diagnosis refined blocker from ui_trigger_executed_but_compare_arg_observation_missing to hook_installed_but_compare_call_not_reached_after_ui_trigger
limitation = pytest_result_summary/status was too optimistic because lint-decision failed after project_state build; this new decision resolves that mismatch by binding to the rebuilt state
```

当前 bottleneck：

```text
stage = compare_real_lhs_provenance_audit
reason = instrumentation_incomplete
blocker = hook_installed_but_compare_call_not_reached_after_ui_trigger
confidence = medium
```

当前 relevant current artifact：

```text
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_hook_readiness_ordering_20260526_r1
latest_artifacts_v2.compare_real_lhs_provenance_audit.path = solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

当前已知 telemetry 摘要：

```text
hook_install_status = installed for all 3 candidates
hook_count/requested_hook_count = 4/4 for all 3 candidates
module_base_resolution_status = resolved
hook_address_validation = resolved for static_compare_callsite 0x258c, pre_compare_lhs_push 0x258b, post_handoff_lhs_reload 0x2559, old_lhs_slot_store 0x253a
hooks_ready_before_ui_trigger = true
ui_trigger_after_hooks_installed = true
ui_trigger_status = button_triggered
python_message_count_total = nonzero for all candidates
python_message_count_by_type = stage + write_monitor_health + hook_install_result only
observation_count = 0
post_ui_observation_count = 0
static_compare_observation_count = 0
helper_observation_count = 0
actual_compare.entry_status = confirmed
actual_compare.arg0/arg1 maps = empty
```

解释边界：

```text
已排除或降低优先级：hook readiness ordering、message bridge dropped observation、aggregation/project_state projection loss。
仍需解释：UI trigger 后为什么没有命中已安装 compare-side hooks。
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

`task_packet.task` / `derived_task` 仍只是状态派生建议；本文件控制当前轮任务。

## 3. Do Not Do

严禁：

```text
1. 不运行 Base64/RC4 breakpoint probe。
2. 不回退旧 sample_solver 盲搜。
3. 不扩大 beam / topN / budget / timeout / frontier iteration。
4. 不启动新的 candidate search。
5. 不追 final writer。
6. 不重复 hook-readiness ordering 修复。
7. 不重复 message bridge / aggregation / project_state projection 诊断，除非新 path audit 直接证明 payload 已发送但被丢弃。
8. 不把 stale compare_probe / stale handoff artifacts 当 current evidence。
9. 不读取完整 solve_reports/。
10. 不读取完整 PROJECT_PROGRESS_LOG.txt。
11. 不提交完整 solve_reports/。
12. 不修改 .codex-skills/、registry、sync 或 agent runtime。
13. 不把动态 runtime facts 写入 .codex-skills/。
14. 不通过删除测试、降低断言或绕过 classification 来制造通过。
15. 不重复 negative_results 中的失败方向，包括 exact2 basin value-pool、H1/H3 fixed contrast set、旧 transform trace consistency、旧 producer material confirmation、Base64/RC4 material producer 假设、旧 [ebp-0x1170] 假设。
```

特别限制：

```text
本轮可以运行一次 bounded rerun，但它不是搜索；它只能验证 UI trigger 后的 path reachability。
本轮不得扩大 current candidates，不得调大 timeout/budget。
本轮不得把 compare_probe fallback 提升为 provenance。
本轮不得把 hook_installed_but_compare_call_not_reached_after_ui_trigger 再原样输出为最终 blocker；必须给出更具体路径结论，除非 runtime precondition 阻断。
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

如果新增 path reachability artifact，允许检查该新 artifact 的 summary/per-candidate JSON。

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史所有 rounds/
```

## 5. Required Audit

Codex 报告必须回答：

```text
1. 当前 sidecar hook set 中 static_compare_callsite 0x258c、pre_compare_lhs_push 0x258b、post_handoff_lhs_reload 0x2559、old_lhs_slot_store 0x253a 是否仍是当前 binary 的 instruction boundary。
2. UI trigger 后是否进入 decrypt handler 或等价 UI event handler；如果不能确认，给出 blocker。
3. handler 进入后是否进入 handoff helper / pre-compare window；如果不能确认，给出具体停止点。
4. 如果 handoff helper 进入但 compare-side hooks 未命中，说明 return path / branch path / exception path 哪一类证据支持“跳过 compare window”。
5. 如果 compare-side hooks 被命中但旧 artifact 未记录 observation，必须重新分类为 payload/bridge/aggregation gap，并给出直接证据。
6. 是否只使用当前 3 个 candidates；必须列出 candidate set。
7. 是否有 stale/missing artifact 被错误当成 current；必须明确说明没有。
8. 是否遵守 negative_results；必须明确说明没有重复禁止方向。
9. pytest_result.txt 正文必须展开 lint-decision、lint-report、git diff --check 的结果，不能只写在 summary。
10. 如果 lint-decision 因 build 后 digest 变化失败，pytest_result_summary.status 不得写 PASSED；应写 PARTIAL，并在 report 中说明需要下一轮刷新 decision。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260527_diagnose_compare_hook_path_not_reached",
  "round_id": "round_20260527_diagnose_compare_hook_path_not_reached",
  "based_on_decision_id": "decision_20260527_diagnose_compare_hook_path_not_reached",
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

允许新增最小 runtime sidecar 或 helper，但必须服务于 path reachability，不得扩展为通用 agent runtime：

```text
reverse_agent/olly_scripts/*compare*path*reachability*.py
reverse_agent/olly_scripts/*ui*path*.py
```

允许新增或更新的 project_state 输出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
project_state/model_gate.json
project_state/rounds/round_20260527_diagnose_compare_hook_path_not_reached/*
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
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "path or reachability or compare or sidecar or ui or trigger or timing or classification"
python -m pytest -q tests/test_project_state.py -k "path or reachability or sidecar or observation or blocker or report or runtime or projection"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <new_or_current_run_name>
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果实际做了 bounded rerun，必须记录完整 rerun command、run_name、artifact path 和 candidate set。

如果没有做 rerun，必须说明为什么仅靠 current artifact/code audit 已足够给出更具体 path blocker。

## 8. Stop Conditions

立即停止并写 report，如果出现任一情况：

```text
1. 已证明 UI trigger 后到达 compare-side path，并获得 compare-side hook hit / observation。
2. 已定位到更具体 path blocker，并有 artifact/code evidence 支撑。
3. runtime 环境无法启动 Frida/pywinauto/target，记录 sidecar_runtime_precondition_failed。
4. 需要扩大 candidate/search/timeout/budget 才能继续，此时不得扩大，必须停止并报告 BLOCKED。
5. 发现关键 artifact missing 或 freshness 非 current，先停止并要求有界重建 project_state。
6. 发现继续推进会重复 negative_results 禁止方向，立即停止。
```

本轮输出必须让下一轮 GPT 能直接判断：UI trigger 后未到达 compare hook，是 UI handler 没进、handler 早退、handoff 未进、handoff return path 跳过 compare、hook 地址 stale，还是 runtime precondition 问题。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260526_diagnose_arg0_observation_delivery",
  "round_id": "round_20260526_diagnose_arg0_observation_delivery",
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

本轮属于 **reverse_solving** 主线，但目标不是搜索 candidate，也不是追 final writer。目标是对当前 blocker `arg0_ui_trigger_or_timeout_blocked` 做 bounded diagnosis，并在必要时做最小代码修复，使下一轮能明确知道 sidecar observation 是被 UI trigger、hook readiness、message bridge、schema projection，还是 artifact aggregation 阶段阻断。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只作为派生建议，不自动覆盖本 decision。

## 1. Goal

诊断并最小修复 `compare_real_lhs_provenance_audit` 的 observation delivery blocker。

必须完成：

```text
1. 读取当前 current artifact：
   solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json

2. 明确解释为什么 actual_compare.entry 已 confirmed / observed_count=3，但 actual_compare.arg0/arg1 为空。

3. 将当前宽泛 blocker：
   arg0_ui_trigger_or_timeout_blocked

   拆成更具体分类之一：
   - hooks_not_ready_before_ui_trigger
   - ui_trigger_not_executed
   - ui_trigger_executed_but_compare_arg_observation_missing
   - message_bridge_dropped_observation
   - sidecar_payload_schema_gap
   - project_state_projection_gap
   - artifact_aggregation_gap
   - inconclusive_with_missing_required_telemetry

4. 如果原因是代码层 schema / aggregation / projection 缺口，做最小修复并加测试。

5. 如果 current artifact 本身缺少必要 telemetry，先补 sidecar/aggregation telemetry，不要直接扩大 runtime 搜索。

6. 只有在完成静态/单测修复后，才允许一次 bounded rerun，用同一批 current candidates 验证 observation delivery；不允许扩大 candidate、beam、topN、timeout、budget。
```

本轮完成标准不是解出 flag，而是把 blocker 从泛化的 `arg0_ui_trigger_or_timeout_blocked` 收敛成一个可审计、可复现、可进入下一轮的具体原因。

## 2. Current Evidence

当前主线：

```text
mainline = reverse_solving
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
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
blocker = arg0_ui_trigger_or_timeout_blocked
confidence = medium
```

当前 candidate evidence：

```text
exact2 candidate_hex = 78d540b49c59077041414141414141
exact2 runtime_ci_exact_wchars = 2
exact2 runtime_ci_distance5 = 246

frontier candidate_hex = 5a3e7f46ddd474d041414141414141
frontier runtime_ci_exact_wchars = 1
frontier runtime_ci_distance5 = 258
```

当前 artifact freshness：

```text
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_bounded_writer_trace_20260525_r1

latest_artifacts_v2.summary.freshness = current
latest_artifacts_v2.run_manifest.freshness = current

latest_artifacts_v2.compare_probe.freshness = stale
latest_artifacts_v2.compare_handoff_return_site_probe.freshness = stale
latest_artifacts_v2.compare_producer_material_confirmation.freshness = stale
latest_artifacts_v2.function_semantic_audit.freshness = stale
```

当前 critical symptom：

```text
latest_compare_real_lhs_provenance_audit.actual_compare.entry = 0x258c
latest_compare_real_lhs_provenance_audit.actual_compare.entry_status = confirmed
latest_compare_real_lhs_provenance_audit.actual_compare.observed_count = 3

但是：
actual_compare.arg0_value_by_candidate = {}
actual_compare.arg0_preview_by_candidate = {}
actual_compare.arg1_value_by_candidate = {}
actual_compare.arg1_preview_by_candidate = {}
arg0_final_data_writer_trace.final_writer_status = final_writer_trace_schema_gap
final_writer_gap_reason = actual_compare_arg0_missing
```

上一轮已接受的前置修复：

```text
compare_aware_search.py 已确认非空且 CompareAwareSearchStrategy 可 import。
compare-aware focused tests passed。
project_state focused tests passed。
pytest_result 与 report/decision 元数据已匹配。
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

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
10. 不把动态 runtime facts 写入 .codex-skills/。
11. 不扩张 skill registry / sync / agent runtime。
12. 不通过删除测试断言来掩盖 observation delivery 缺口。
```

特别注意：

```text
本轮可以 inspect 当前 run 的 bounded artifact，但不能扫描完整 solve_reports。
本轮可以修复 sidecar / aggregation / project_state projection，但不能推进解题搜索。
本轮只有在静态诊断和测试完成后，才允许一次 bounded rerun 验证当前 blocker。
```

## 4. Files To Inspect

必须检查：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt

reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
reverse_agent/sidecar_health.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界检查当前 run artifact：

```text
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\summary.json
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\run_manifest.json
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\case_results\samplereverse-compare-producer-backtrace.json
solve_reports\harness_runs\sr_arg0_bounded_writer_trace_20260525_r1\reports\tool_artifacts\samplereverse_patched\compare_real_lhs_provenance_audit\compare_real_lhs_provenance_audit.json
```

必要时检查：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/*compare*lhs* 或 compare_aware_search.py 引用到的具体 Olly/sidecar script template
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
1. current artifact 中是否已经包含 lifecycle / hook readiness / UI trigger / message callback / observation count 字段。

2. actual_compare.entry confirmed 但 arg0/arg1 为空，是以下哪一类：
   - hook 没装好；
   - UI trigger 没执行；
   - UI trigger 执行但 compare arg hook 没上报；
   - Python message bridge 收到消息但丢字段；
   - sidecar payload schema 没解析；
   - aggregation 丢失 candidate rows；
   - project_state projection 丢失字段；
   - current artifact telemetry 不足，无法判断。

3. 如果 artifact 中已有 raw observation，但 project_state/current_state 没投影，必须修复 project_state projection。

4. 如果 sidecar_health classification 过粗，必须补充 classification normalization，使其能输出更具体 blocker。

5. 如果 compare_aware_search aggregation 丢失字段，必须修复 aggregation，不允许只改报告文字。

6. 如果 current artifact 缺少必要 telemetry，必须指出缺少哪些字段，并补单测防止未来继续生成不可诊断 artifact。

7. 是否需要 bounded rerun；若需要，必须说明 rerun 只使用 current candidates，不扩大搜索。
```

报告顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260526_diagnose_arg0_observation_delivery",
  "round_id": "round_20260526_diagnose_arg0_observation_delivery",
  "based_on_decision_id": "decision_20260526_diagnose_arg0_observation_delivery",
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

仅在确认为 sidecar script telemetry 缺失时，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
或 compare_aware_search.py 实际引用的 compare_real_lhs_provenance sidecar script/template
```

允许新增的测试方向：

```text
1. mock artifact: entry confirmed but arg0 missing -> classify as specific blocker, not generic inconclusive。
2. mock artifact: lifecycle shows hooks not ready before UI trigger -> classify hooks_not_ready_before_ui_trigger。
3. mock artifact: ui trigger start/end exists but no compare arg observation -> classify ui_trigger_executed_but_compare_arg_observation_missing。
4. mock artifact: raw observation exists but projected current_state drops it -> test project_state projection keeps it。
5. mock artifact: sidecar payload has candidate rows but aggregation drops them -> test aggregation preserves them。
```

允许生成或更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
project_state/model_gate.json
```

如果执行 bounded rerun，允许生成一个新 harness run，例如：

```text
sr_arg0_observation_delivery_20260526_r1
```

但必须满足：

```text
1. 只跑当前 3 个已知 candidates。
2. 不扩大 timeout/budget。
3. 不跑 Base64/RC4 probe。
4. 不启动 search。
5. 不提交完整 solve_reports。
6. 只通过 project_state index 引用新 artifact。
```

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/project_state.py reverse_agent/sidecar_health.py

python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or observation or sidecar or ui or trigger or timeout or lifecycle or classification"

python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime or projection"

python -m pytest -q tests/test_project_state.py

python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1

python -m reverse_agent.project_state lint-decision --state-dir project_state

python -m reverse_agent.project_state status --state-dir project_state

python -m reverse_agent.project_state lint-report --state-dir project_state

git diff --check
```

如果执行 bounded rerun，还必须追加记录：

```text
1. 实际 rerun command。
2. 新 run_name。
3. 新 compare_real_lhs_provenance_audit path。
4. 新 artifact freshness 是否为 current。
5. 新 classification 是否比 arg0_ui_trigger_or_timeout_blocked 更具体。
```

如果没有执行 bounded rerun，必须明确说明：

```text
rerun skipped because artifact-only/code-level diagnosis was sufficient
```

或者：

```text
rerun skipped because current artifact lacks safe preconditions; next decision must explicitly authorize bounded rerun
```

## 8. Stop Conditions

遇到以下情况立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 需要读取完整 solve_reports/ 才能继续。
2. 需要 PROJECT_PROGRESS_LOG.txt 才能继续。
3. 需要 Base64/RC4 runtime probe 才能继续。
4. 需要扩大 candidate、beam、topN、timeout、budget 才能继续。
5. current artifact 不是 current，或 source_run 不匹配 sr_arg0_bounded_writer_trace_20260525_r1。
6. 无法区分 artifact 缺字段和 project_state projection 丢字段。
7. 修复只能靠删除测试、降低断言或绕过 classification。
8. bounded rerun 需要生成大范围 solve_reports 提交。
9. lint-decision / lint-report / pytest_result 元数据无法与本 decision_id 对齐。
```

本轮成功标准：

```text
1. blocker 从 arg0_ui_trigger_or_timeout_blocked 收敛为更具体分类；
2. 相关 parser / sidecar_health / project_state projection 有测试覆盖；
3. current artifact freshness 未被误用；
4. report 与 pytest_result 元数据匹配；
5. 没有推进搜索、没有 Base64/RC4 probe、没有 final-writer chase。
```

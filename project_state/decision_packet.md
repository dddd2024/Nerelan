```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260526_rework_restore_compare_aware_search",
  "round_id": "round_20260526_rework_restore_compare_aware_search",
  "based_on_state_build_id": "state_20260526_091652_bce32934a6b5",
  "based_on_state_digest": "bce32934a6b55d4808d9580e6f1ecf87e24c13a2c137cd767fb3dc79cec308b9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮是上一轮审计后的 **返工修复任务**。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`，不是 `project_state/task_packet.json` 中的 `task` 或 `derived_task`。

本轮仍属于 **reverse_solving** 主线，但目标不是推进逆向解题，而是修复当前 GitHub committed tree 的一致性问题：`reverse_agent/strategies/compare_aware_search.py` 在当前 main 上为空，导致上一轮报告中的测试通过结论与提交状态不可信。

## 1. Goal

恢复并验证 `reverse_agent/strategies/compare_aware_search.py` 的有效内容，重新应用上一轮必要的 UI trigger timing / sidecar health 聚合改动，使当前 committed tree 与报告、测试结果重新一致。

必须完成：

```text
1. 恢复 reverse_agent/strategies/compare_aware_search.py 到上一轮可用的非空版本。
2. 保留或重新应用上一轮合理的 UI trigger timing / sidecar health aggregation 改动。
3. 证明 tests/test_compare_aware_search_strategy.py 中的大量 import 在当前 committed tree 下可以正常执行。
4. 重新运行并记录真实测试结果。
5. 更新 codex_execution_report.md 和 pytest_result.txt，使其与本 decision_id 匹配。
```

本轮不是 final writer 追踪任务，不生成新的解题结论。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 state 基础：

```text
state_build_id = state_20260526_080937_c7583ea6dc32
state_digest = c7583ea6dc3287378a856af210a6f00853908844427ad5673fa0d652872faac9
profile = samplereverse
source_harness_run = sr_arg0_bounded_writer_trace_20260525_r1
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = inconclusive
current_bottleneck.blocker = arg0_ui_trigger_or_timeout_blocked
workflow_status = REPORT_AVAILABLE
review_status = PENDING_REVIEW
```

`task_packet.task` / `task_packet.derived_task` 当前只能作为派生建议。本轮执行权威是本 `decision_packet.md`。

上一轮审计结论：**REWORK_REQUIRED**。

阻断性证据：

```text
reverse_agent/strategies/compare_aware_search.py 当前 GitHub main 内容为空。
empty blob sha = db45c3c1b692ede76c6d39c20f1d209affeefd68
```

而 `tests/test_compare_aware_search_strategy.py` 仍从该文件导入大量符号，包括：

```text
CompareAwareSearchStrategy
COMPARE_REAL_LHS_PROVENANCE_AUDIT_FILE_NAME
COMPARE_PRE_COMPARE_HANDOFF_TARGET_PROBE_FILE_NAME
build_compare_real_lhs_provenance_audit_payload
run_compare_real_lhs_provenance_audit
run_compare_pre_compare_handoff_target_probe
validate_compare_aware_results
resolve_compare_aware_anchors
```

因此，上一轮 `pytest_result.txt` 中记录的 compare-aware tests passed 与当前 GitHub committed tree 不一致，不能接受。

上一轮可保留的正向实现方向：

```text
1. compare_pre_compare_handoff_target_probe.py 增加 hooks installed readiness barrier。
2. Python message callback 仍在 script.load 前注册。
3. UI trigger 前等待 hooks_installed message，但不能扩大 timeout/budget。
4. sidecar lifecycle 增加 hooks_ready_before_ui_trigger、ui_trigger_start/end、timeout_or_wait_reason 等字段。
5. sidecar_health.py 增加 lifecycle / hook_install / message_bridge / observations / classification 归一化。
6. project_state.py 增加 UI timing blocker 分类投影。
```

当前 artifact freshness：

```text
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.compare_probe.freshness = stale
```

不能把 stale `compare_probe` 当 current evidence。

当前 skill_profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

## 3. Do Not Do

严禁：

```text
1. 不运行 Base64/RC4 probe。
2. 不回退到旧 sample_solver 盲搜。
3. 不扩大 beam / topN / budget / timeout / frontier iteration。
4. 不启动新的 candidate search。
5. 不追 final writer。
6. 不默认读取完整 solve_reports/。
7. 不提交完整 solve_reports/。
8. 不把 stale / missing artifact 当 current evidence。
9. 不把动态 runtime facts 写入 .codex-skills/。
10. 不扩张 skill registry / sync / agent runtime。
11. 不继续推进解题，直到 compare_aware_search.py 恢复并通过测试。
```

## 4. Files To Inspect

必须检查：

```text
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/sidecar_health.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必要时检查：

```text
当前 git diff
git log -- reverse_agent/strategies/compare_aware_search.py
上一轮可用提交中的 reverse_agent/strategies/compare_aware_search.py
```

不要默认读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

Codex 必须在报告中明确回答：

```text
1. compare_aware_search.py 为什么在 GitHub 当前 main 上为空。
2. 这是否是误提交、合并错误、脚本写入错误、还是工具读取异常。
3. 恢复后的 compare_aware_search.py 是否非空。
4. 恢复后的文件是否包含 CompareAwareSearchStrategy 和测试中导入的关键符号。
5. 上一轮 UI trigger timing / sidecar health aggregation 改动是否仍存在。
6. tests/test_compare_aware_search_strategy.py 是否能在当前 committed tree 下真实导入并运行。
7. codex_execution_report.md 的 based_on_decision_id 是否等于本轮 decision_id。
8. pytest_result.txt 的 decision_id / report_id / round_id 是否与本轮匹配。
```

报告顶部必须包含 `codex_report_summary` fenced JSON block，且：

```text
based_on_decision_id = decision_20260526_rework_restore_compare_aware_search
round_id = round_20260526_rework_restore_compare_aware_search
```

如果只恢复文件但未重新运行测试，不能标记 SUCCESS。

## 6. Implementation Scope

允许的改动范围：

```text
1. reverse_agent/strategies/compare_aware_search.py
   - 恢复上一轮可用内容。
   - 重新应用必要的 UI trigger timing / sidecar health aggregation 字段传播。
   - 保证 tests/test_compare_aware_search_strategy.py 的 import 符号全部存在。

2. reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
   - 仅在发现上一轮 timing telemetry 改动被破坏时做最小修复。
   - 保持 callback-before-load 和 hooks-ready barrier。

3. reverse_agent/sidecar_health.py
   - 仅允许为 compare_aware_search.py 聚合字段做兼容性修复。

4. reverse_agent/project_state.py
   - 仅允许修复 UI timing blocker projection 的明显不一致。

5. tests/test_compare_aware_search_strategy.py / tests/test_project_state.py
   - 只允许补充或修正针对恢复内容的测试。
   - 不允许通过删除 import 或降低断言来掩盖 compare_aware_search.py 为空的问题。

6. project_state/codex_execution_report.md / project_state/pytest_result.txt
   - 必须更新为本轮真实执行结果。
```

不要求也不允许本轮生成新 runtime artifact。

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py reverse_agent/sidecar_health.py

python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or hook or timeout or observation or ui or trigger or timing or classification"

python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime"

python -m pytest -q tests/test_project_state.py

python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_bounded_writer_trace_20260525_r1

python -m reverse_agent.project_state lint-decision --state-dir project_state

python -m reverse_agent.project_state status --state-dir project_state

python -m reverse_agent.project_state lint-report --state-dir project_state

git diff --check
```

强烈建议额外运行：

```text
python - <<'PY'
from reverse_agent.strategies.compare_aware_search import CompareAwareSearchStrategy
print(CompareAwareSearchStrategy.__name__)
PY
```

如果恢复后 import 仍失败，立即停止并报告 `REWORK_REQUIRED`，不要继续改 project_state 假装通过。

## 8. Stop Conditions

出现以下任一情况必须停止并报告：

```text
1. 无法恢复 compare_aware_search.py 的上一轮可用内容。
2. compare_aware_search.py 恢复后仍为空或核心符号缺失。
3. tests/test_compare_aware_search_strategy.py 无法导入 compare_aware_search。
4. Codex 无法解释为什么上一轮报告中的测试通过与当前 committed tree 冲突。
5. 需要读取完整 solve_reports/ 才能继续。
6. 需要运行 runtime probe 才能继续。
7. 任何测试失败且无法在本轮最小范围内修复。
```

本轮完成标准：当前 GitHub committed tree 中 `compare_aware_search.py` 恢复为非空有效策略文件，compare-aware 与 project_state 测试真实通过，report/pytest 元数据与本 decision 匹配。

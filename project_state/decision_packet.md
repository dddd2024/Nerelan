```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260528_fix_material_hook_utf16_kind_protocol",
  "round_id": "round_20260528_fix_material_hook_utf16_kind_protocol",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮属于 **reverse_solving** 主线，但任务是一个窄范围 correctness repair：修复 `material_hook_runtime_validation` 的 ACCEPT 路径与 `base64_rc4_breakpoint_probe` 之间的 UTF-16LE static point kind 协议不一致问题。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 是状态派生建议，不自动覆盖本 decision。

## 1. Goal

修复 material-hook validation ACCEPT 后续路径中的协议 bug：

```text
material_hook_runtime_validation validated hook semantic kind = utf16le_payload
base64_rc4_breakpoint_probe downstream protocol kind = utf16le
```

当前下游脚本 `reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py` 中 `_hook_results_from_events()` 只在 `point_kind == "utf16le"` 时把 material 计入 `hook_results["utf16le_payload"] = "inferred"`。因此，若上游把 static point 的 `kind` 写成 `utf16le_payload`，ACCEPT 路径即使命中 hook，也可能被误分类为 `breakpoint_probe_partial` 或 material unavailable。

本轮目标是让 material validation 生成的 static point 同时满足：

```text
1. 下游 probe 协议字段 kind 使用 utf16le。
2. 上游语义字段保留 utf16le_payload，例如 material_kind 或 semantic_kind。
3. 现有 gating 仍以 validated material hook 为前提，不放宽到未验证 hook。
4. 单元测试覆盖 ACCEPT 后 static point kind 映射和下游 hook result 归一化。
```

本轮不要求重新跑真实 samplereverse runtime harness；重点是修复代码协议和测试覆盖。

## 2. Current Evidence

当前主线：

```text
mainline = reverse_solving
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_mainline = L15(prefix8)
```

当前 project_state：

```text
state_build_id = state_20260527_153028_1d6dd81ecbd6
state_digest = 1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02
source_run = sr_arg0_hook_readiness_ordering_20260526_r1
current_bottleneck.stage = compare_hook_path_reachability_audit
current_bottleneck.reason = decrypt_handler_entered_but_candidate_path_exits_before_handoff
```

当前 `task_packet.task` / `derived_task`：

```text
task = Diagnose bounded compare hook path reachability
derived_task = Diagnose bounded compare hook path reachability
```

这些是当前状态派生建议，不是本轮实际执行任务。本轮由本 `decision_packet.md` 控制。

相关 artifact freshness：

```text
latest_artifacts_v2.compare_hook_path_reachability_audit.freshness = current
latest_artifacts_v2.compare_hook_path_reachability_audit.source_run = sr_arg0_hook_readiness_ordering_20260526_r1
latest_artifacts_v2.material_hook_runtime_validation.freshness = missing
latest_artifacts_v2.base64_rc4_breakpoint_probe.freshness = missing
latest_artifacts_v2.base64_rc4_static_point_discovery.freshness = stale
```

当前证据说明：

```text
1. material_hook_runtime_validation 当前没有 current runtime artifact；不能把旧 PR 的 partial run 当作当前 runtime 证据。
2. base64_rc4_breakpoint_probe 当前 missing；本轮不应运行新的 Base64/RC4 runtime probe。
3. base64_rc4_static_point_discovery 是 stale，只能作为协议/历史上下文，不可作为当前 runtime evidence。
4. 这次修复来自代码协议审计：下游 base64_rc4_breakpoint_probe 的 _hook_results_from_events() 当前只识别 point_kind == "utf16le"。
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
2. 不运行新的 reverse runtime probe 或 harness rerun，除非现有单元测试已经无法覆盖纯协议路径；即便需要，也必须先在 report 中标为 blocked 而不是擅自扩大 runtime。
3. 不扩大 candidate set、beam、topN、budget、timeout、frontier iteration。
4. 不回退旧 sample_solver 盲搜。
5. 不追 final writer。
6. 不把 stale base64_rc4_static_point_discovery 或 missing material_hook_runtime_validation 当 current evidence。
7. 不读取完整 solve_reports/。
8. 不读取完整 PROJECT_PROGRESS_LOG.txt。
9. 不修改 `.codex-skills/`、registry、sync 或 agent runtime。
10. 不通过修改下游 `base64_rc4_breakpoint_probe.py` 放宽所有 unknown kind 来绕过协议问题。
11. 不删除或削弱现有 gating 测试。
12. 不提交完整 solve_reports/。
```

特别限制：

```text
本轮是协议修复，不是解题推进。修复点应尽量小，并保持 material validation 必须 ACCEPT 后才可生成可用于 Base64/RC4 probe 的 static points。
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
reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

可以有界检查：

```text
reverse_agent/project_state.py
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
1. 当前 `_breakpoint_static_points_from_material_hook_runtime_validation_payload()` 或等价函数是否把 `kind` 写成 `utf16le_payload`。
2. 当前 `base64_rc4_breakpoint_probe.py` 是否仍只在 `point_kind == "utf16le"` 时设置 `hook_results["utf16le_payload"]`。
3. 修复后传给下游 probe 的 static point 是否为 `kind="utf16le"`。
4. 修复后是否仍保留上游语义字段，例如 `material_kind="utf16le_payload"`。
5. 修复是否只影响 material-hook validation ACCEPT -> Base64/RC4 static point handoff，不影响 BLOCKED/REJECTED gating。
6. 是否没有运行 Base64/RC4 probe、没有扩大搜索、没有使用 stale/missing artifact 作为 current evidence。
7. 是否遵守 negative_results。
8. `codex_execution_report.md` 顶部必须包含 `codex_report_summary`，且 `based_on_decision_id` 必须等于 `decision_20260528_fix_material_hook_utf16_kind_protocol`。
9. `pytest_result.txt` 必须记录实际测试结果，不能只写摘要。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时允许修改：

```text
reverse_agent/project_state.py
```

不建议修改：

```text
reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
```

除非审计证明更正确的修复点在下游脚本；如果修改下游脚本，必须保留现有 `utf16le` 协议兼容，并新增回归测试证明不会误把任意 unknown kind 当 material。

推荐实现方式：

```text
1. 在 material-hook validation -> static point 转换处增加映射：
   semantic material_kind / kind = utf16le_payload
   downstream static point kind = utf16le

2. 保留 hook payload 中的语义字段：
   material_kind = utf16le_payload
   semantic_kind = utf16le_payload   # 可选

3. 新增测试：
   - 构造 material validation ACCEPT payload。
   - 调用 `_breakpoint_static_points_from_material_hook_runtime_validation_payload()`。
   - 断言返回 static point 位于 `static_points["utf16le_payload"]` 或现有容器结构中，但 point 内部下游协议 `kind == "utf16le"`。
   - 断言保留 `material_kind == "utf16le_payload"`。
   - 通过 base64_rc4_breakpoint_probe 的 `_hook_results_from_events()` 或等价公开路径验证 `point_kind="utf16le"` 会得到 `hook_results["utf16le_payload"] == "inferred"`。

4. 如现有测试已经导入私有函数，允许继续使用私有函数做窄回归；否则通过较高层 runner fake subprocess 覆盖。
```

## 7. Tests

必须运行：

```text
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/base64_rc4_breakpoint_probe.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "material_hook or base64_rc4 or breakpoint or utf16"
python -m pytest -q tests/test_project_state.py -k "material_hook or report or lint"
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果 Codex 修改了 `project_state` 或新增 report/test summary，还必须运行：

```text
python -m reverse_agent.project_state lint-report --state-dir project_state
```

不要求运行：

```text
python -m pytest -q
真实 samplereverse harness
Base64/RC4 runtime breakpoint probe
```

如果 Codex 认为必须运行 broader pytest，允许运行，但不能以 broader pytest 替代上述 focused tests。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 找不到 material-hook validation 到 Base64/RC4 static point 的转换函数。
2. 当前主干代码已经没有该协议问题，但测试无法证明；此时只新增回归测试和报告，不做无意义重写。
3. 需要真实 runtime artifact 才能判断协议修复是否正确。
4. lint-decision 显示本 decision 的 digest/meta 不匹配，且无法在本轮安全修复。
```

完成条件：

```text
1. ACCEPT path 中传给 downstream Base64/RC4 probe 的 static point 使用 `kind="utf16le"`。
2. 上游语义仍保留 `utf16le_payload`。
3. BLOCKED/REJECTED 不放行 Base64/RC4 probe。
4. focused tests 覆盖该协议映射。
5. codex_execution_report.md、pytest_result.txt 与本 decision_id 对齐。
6. lint-report 通过；lint-decision 若因本轮 build 后 digest 变化失败，必须在 pytest_result 和 report 中明确标为 PARTIAL，不得写 PASSED。
```

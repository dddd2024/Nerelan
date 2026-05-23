```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_round_manifest_consistency",
  "round_id": "round_20260523_engineering_round_manifest_consistency",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

上一轮工程审计结论是 `ACCEPTED_WITH_LIMITATIONS`：`pytest_result_summary.tests_ran` 已覆盖 `codex_report_summary.tests_ran`，validator / status / lint-report 都已经暴露 coverage 状态；但 `lint-report` 仍长期带着两个 warning：

```text
report round_id does not match current_state.round_id
round_manifest missing
```

本轮只处理这两个 warning 背后的协作语义：明确工程协作 round、样本状态 round、round_manifest 归档状态之间的边界。不要改逆向逻辑，不要运行 runtime probe，不要处理历史大文件解除跟踪。

## 1. Goal

本轮目标：

```text
1. 明确 round_id 语义：
   - decision_meta.round_id / codex_report_summary.round_id 表示 GPT-Codex 协作轮次。
   - current_state.round_id 表示当前样本/证据状态构建轮次，尤其在 state_scope=sample_state 时不必等于工程协作 round。
2. 修改 lint-report，使它优先检查 codex_report_summary.round_id 是否匹配 decision_meta.round_id。
3. 不再把工程支线 report.round_id 与 sample current_state.round_id 不一致作为默认 warning；改为结构化字段暴露：
   - report_decision_round_id_match
   - report_current_state_round_relation
   - current_state_round_id
4. 明确 round_manifest missing 语义：
   - 如果当前 round 尚未 archive-round，则报告为 archive_status=not_archived，而不是模糊 warning。
   - 如果 report 已声明 generated_artifacts 或归档要求，但 manifest 缺失，应能清楚标出。
5. 在 status / lint-report 中输出 round/manifest 结构化字段，减少 GPT 审计时的歧义。
6. 增加 tests/test_project_state.py 覆盖工程支线 round 与 sample current_state.round_id 不一致但合法、decision/report round mismatch、manifest missing、manifest present 等情况。
```

本轮要解决的是“warning 语义不清楚”，不是强行让所有 round_id 相等。

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

`task_packet.json` 仍来自 `samplereverse` 样本状态，`task_packet.task` / `derived_task` 是逆向主线派生建议，不是本轮工程任务。`task_packet.execution_scope` 为 `decision_packet_controls_current_round`，因此本轮 Codex 实际执行权威仍是 `project_state/decision_packet.md`。

当前 `current_state.json` 是样本状态：

```text
state_scope = sample_state
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
```

这代表逆向证据状态，不代表每个工程支线 decision 的协作 round。

上一轮有效报告：

```text
report_id = report_20260523_engineering_pytest_tests_ran_consistency
round_id = round_20260523_engineering_pytest_tests_ran_consistency
based_on_decision_id = decision_20260523_engineering_pytest_tests_ran_consistency
status = SUCCESS
```

上一轮 `pytest_result.txt` 已经证明：

```text
report_tests_ran_count=5
pytest_result_tests_ran_count=5
pytest_result_tests_cover_report=True
pytest_result_missing_report_tests=[]
```

但 lint-report 仍保留：

```text
warnings: report round_id does not match current_state.round_id; round_manifest missing
```

这两个 warning 现在已经不是失败信号，而是协作语义尚未建模清楚。

artifact freshness 说明：

```text
本轮不依赖 solve_reports 逆向 artifact。
artifact_index.latest_artifacts_v2 中的 stale/missing 逆向 artifact 不应触发 runtime probe。
不要因为 current_state 的 sample round 较旧就重跑逆向 harness。
```

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 逆向 sidecar。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何 runtime probe。
不要扩大 beam、budget、timeout、topN、frontier iteration。
不要读取完整 solve_reports。
不要修改 PROJECT_PROGRESS_LOG.txt。
不要修改 reverse_agent/olly_scripts/*。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要继续扩展 sidecar_health schema。
不要处理历史 round 大文件解除跟踪；不要执行 git rm --cached。
不要把 current_state.round_id 改成工程支线 round_id。
不要删除 active project_state/*.json。
不要把 task_packet.task 当成本轮执行目标。
不要新增重型依赖、数据库、调度平台或外部服务。
不要让本轮 diff 超过 500 行；若超过，停止并报告原因。
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
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/task_packet.json
reverse_agent/project_state.py
tests/test_project_state.py
```

必要时检查：

```text
project_state/rounds/<current report round_id>/round_manifest.json
project_state/negative_results.json
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
project_state/rounds/* 历史全量目录
reverse_agent/olly_scripts/*
reverse_agent/strategies/compare_aware_search.py
```

## 5. Required Audit

Codex 修改前必须先完成并在报告中记录以下审计：

```text
1. 读取当前 decision_meta.round_id。
2. 读取当前 codex_report_summary.round_id。
3. 读取 current_state.round_id 与 current_state/state_scope。
4. 说明为什么工程支线 report.round_id 不应强制等于 sample current_state.round_id。
5. 检查当前 lint_report 中 round_id mismatch 的判断逻辑。
6. 检查当前 lint_report 中 round_manifest missing 的判断逻辑。
7. 检查 project_state/rounds/<report_round_id>/round_manifest.json 是否存在。
8. 确认本轮不需要读取 solve_reports。
9. 确认本轮不会运行任何逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：round_id 关系建模

在 `reverse_agent/project_state.py` 中给 lint/status 增加轻量 helper，名称可按现有风格决定，例如：

```text
build_round_consistency(decision, report, current_state, state_dir) -> dict
```

最低返回字段：

```text
report_round_id
decision_round_id
current_state_round_id
current_state_scope
report_decision_round_id_match: true/false/unknown
report_current_state_round_relation: "same" | "different_but_allowed_sample_state" | "different_unclassified" | "unknown"
round_manifest_path
round_manifest_present: true/false
archive_status: "archived" | "not_archived" | "unknown"
round_manifest_warning: string
```

语义要求：

```text
1. 如果 decision_meta.round_id 和 codex_report_summary.round_id 都存在且不同，应作为 lint-report error 或明确 warning；建议 error。
2. 如果 report.round_id 与 current_state.round_id 不同，但 current_state 或 task_packet 表明这是 sample_state / derived_from_sample_artifacts / 工程支线，则不要再输出旧的模糊 warning：report round_id does not match current_state.round_id。
3. 改为输出结构化状态：report_current_state_round_relation=different_but_allowed_sample_state。
4. 如果 current_state_scope 无法判断，则保留 warning，但要输出 relation=different_unclassified。
```

### Phase B：round_manifest missing 语义化

更新 `lint_report()`：

```text
1. 继续检查 project_state/rounds/<report_round_id>/round_manifest.json。
2. 如果不存在，不再只输出 round_manifest missing。
3. 输出 archive_status=not_archived。
4. 是否 warning 由语义决定：
   - 当前 report 还没有执行 archive-round：可以 warning，但描述为 report round not archived yet。
   - 如果 manifest 存在但缺少 pytest_result.txt 或 codex_execution_report.md，继续 warning。
5. 不要自动执行 archive-round。
6. 不要默认创建 round_manifest.json，除非现有测试和函数已有安全 helper，且不造成 Git 生成物污染。
```

### Phase C：status / lint-report 输出

更新 `status_summary()` 与 `_print_status()`，输出：

```text
report_round_id
decision_round_id
current_state_round_id
current_state_scope
report_decision_round_id_match
report_current_state_round_relation
round_manifest_present
archive_status
round_manifest_path
```

更新 `lint_report()` 与 `_print_lint_report()`，输出同类字段。

要求：

```text
1. 旧字段尽量保留兼容。
2. 原来的 warning 文案 report round_id does not match current_state.round_id 应被替换或降级为结构化 relation，不应在工程支线样本状态场景继续出现。
3. round_manifest missing 应替换为更清楚的 report round not archived yet 或 archive_status=not_archived。
```

### Phase D：测试

更新 `tests/test_project_state.py`，覆盖：

```text
1. decision.round_id == report.round_id，current_state.round_id 不同且 state_scope=sample_state：lint-report 通过，不输出旧 round_id mismatch warning，relation=different_but_allowed_sample_state。
2. decision.round_id != report.round_id：lint-report 返回 error 或明确 warning，report_decision_round_id_match=False。
3. round_manifest 不存在：archive_status=not_archived，round_manifest_present=False，warning 文案清晰。
4. round_manifest 存在且包含 pytest_result.txt / codex_execution_report.md：archive_status=archived，round_manifest_present=True。
5. status_summary 输出 round consistency 字段。
6. legacy current_state 缺少 state_scope 时，不崩溃，relation=unknown 或 different_unclassified。
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py -k "round or manifest or lint_report or status"
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

不需要运行：

```bash
tests/test_compare_aware_search_strategy.py
tests/test_sidecar_health.py
任何 samplereverse runtime probe
```

除非 Codex 越界修改了相关文件；若修改了，必须说明原因并运行对应测试。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. 当前 decision_packet.md 缺失 decision_meta。
2. 当前 codex_execution_report.md 缺失 codex_report_summary。
3. 需要改写 current_state.round_id 才能消除 warning。
4. 需要自动执行 archive-round 或创建大量 round 文件才能继续。
5. 需要读取完整 solve_reports 才能继续。
6. 需要运行逆向 runtime probe 才能构造测试。
7. 为了 round consistency 需要大规模重写 project_state.py。
8. 本轮 diff 超过 500 行，且主要不是 tests/test_project_state.py。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，字段要求：

```text
report_id = report_20260523_engineering_round_manifest_consistency
round_id = round_20260523_engineering_round_manifest_consistency
based_on_decision_id = decision_20260523_engineering_round_manifest_consistency
status = SUCCESS / PARTIAL / FAILED / BLOCKED
tests_ran = 真实运行命令列表
generated_artifacts = 本轮更新的 project_state 文件列表
```

报告正文必须明确记录：

```text
1. 修改前 round_id mismatch warning 来源。
2. 修改后 report.round_id 与 decision.round_id 是否匹配。
3. 修改后 report.round_id 与 current_state.round_id 的 relation 如何表达。
4. round_manifest 是否存在，archive_status 是什么。
5. 是否仍存在 warning；如果存在，是否为预期 warning。
6. 是否没有运行任何逆向 runtime probe。
7. 真实测试命令和结果。
8. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- decision.round_id 与 report.round_id 的匹配被显式检查。
- 工程支线 report.round_id 与 sample current_state.round_id 不同不再产生旧的模糊 mismatch warning。
- status / lint-report 输出 round relation 与 archive_status。
- round_manifest missing 被语义化为 not_archived 或清晰 warning。
- tests/test_project_state.py 相关测试通过。
- 未运行任何逆向 runtime probe。
- diff 控制在 500 行内。

ACCEPTED_WITH_LIMITATIONS：
- round relation 建模完成，但 round_manifest 仍未归档，只保留 archive_status=not_archived warning。

REWORK_REQUIRED：
- 仍然用 report round_id does not match current_state.round_id 作为工程支线默认 warning。
- decision.round_id 与 report.round_id 不匹配却未被检测。
- 为消除 warning 修改了 current_state.round_id。
- 自动创建大量 round 文件或重新引入 archive 生成物污染。
- 运行了逆向 runtime probe。
- 缺少测试或测试记录无法对应当前 decision。

BLOCKED：
- 当前 report/decision meta 缺失，无法建立 round 关系。
- 仓库内无法区分 sample_state round 与 collaboration round。
```

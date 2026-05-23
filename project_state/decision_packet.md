```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_pytest_tests_ran_consistency",
  "round_id": "round_20260523_engineering_pytest_tests_ran_consistency",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

上一轮审计结论是 `ACCEPTED_WITH_LIMITATIONS`：`pytest_result.txt` 已经有 `pytest_result_summary` header，且 active 文件不再混入上一轮逆向 runtime 记录；但 `pytest_result_summary.tests_ran` 只记录了 3 条命令，而 `codex_report_summary.tests_ran` 记录了 5 条命令，缺少 `status` 与 `lint-report` 两条验证命令。下一步只补齐这个可信测试证据一致性问题。

## 1. Goal

本轮目标：

```text
1. 让 pytest_result_summary.tests_ran 与 codex_report_summary.tests_ran 保持一致，或者至少由 validator 明确报告二者差异。
2. 更新 validate_pytest_result_for_report，使它能检查 pytest_result_summary.tests_ran 是否覆盖 report_summary.tests_ran。
3. 在 status / lint-report 中暴露 tests_ran 覆盖状态，例如：
   - pytest_result_tests_ran_count
   - report_tests_ran_count
   - pytest_result_tests_cover_report: true/false/unknown
   - pytest_result_missing_report_tests: list[str]
4. 更新 active project_state/pytest_result.txt，使 header 中 tests_ran 覆盖当前报告声明的全部验证命令。
5. 增加 tests/test_project_state.py 用例覆盖：完全覆盖、缺少命令、legacy 无 header、report tests_ran 为空等情况。
```

本轮不是大重构；只补一个一致性检查缺口。

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

`task_packet.json` 仍来自 `samplereverse` 样本状态，`task_packet.task` / `derived_task` 是逆向主线派生建议，不是本轮工程任务。本轮 Codex 实际执行权威以 `project_state/decision_packet.md` 为准。

上一轮有效报告：

```text
report_id = report_20260523_engineering_pytest_result_provenance
based_on_decision_id = decision_20260523_engineering_pytest_result_provenance
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮 `codex_report_summary.tests_ran` 声明运行了 5 条命令：

```text
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q tests\test_project_state.py -k "archive or pytest_result or report"
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

当前 `project_state/pytest_result.txt` 的 `pytest_result_summary.tests_ran` 只记录了前 3 条：

```text
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q tests\test_project_state.py -k "archive or pytest_result or report"
```

因此当前 header 能证明主要 pytest 已运行，但不能完整证明 `status` / `lint-report` 两条审计命令也属于当前轮测试证据。

上一轮 `lint-report` 已能输出 `pytest_result_matches_report: True`，但仍有 warning：

```text
round_id mismatch
round_manifest missing
```

这两个 warning 暂时不作为本轮目标。本轮只处理 `tests_ran` 覆盖一致性。

artifact freshness 说明：

```text
本轮不依赖 solve_reports 逆向 artifact。
artifact_index.latest_artifacts_v2 中的 stale/missing 逆向 artifact 不应触发 runtime probe。
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
不要把 round_manifest missing 作为本轮目标。
不要新增 archive-round 行为变更。
不要删除 active project_state/*.json。
不要把 task_packet.task 当成本轮执行目标。
不要引入数据库、调度平台、外部服务或重型依赖。
不要让本轮 diff 超过 400 行；若超过，停止并报告原因。
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
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/decision_packet.md
reverse_agent/project_state.py
tests/test_project_state.py
```

必要时检查：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/negative_results.json
```

不要默认检查：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
project_state/rounds/*
reverse_agent/olly_scripts/*
reverse_agent/strategies/compare_aware_search.py
```

## 5. Required Audit

Codex 修改前必须先完成并在报告中记录以下审计：

```text
1. 读取当前 codex_execution_report.md，提取 codex_report_summary.tests_ran。
2. 读取当前 pytest_result.txt，提取 pytest_result_summary.tests_ran。
3. 对比两组命令，列出 pytest_result_summary 缺少哪些 report tests。
4. 确认当前 pytest_result_summary.decision_id 与 codex_report_summary.based_on_decision_id 是否匹配。
5. 确认 project_state.py 当前 validate_pytest_result_for_report 是否检查 tests_ran 覆盖关系。
6. 确认本轮不需要读取 solve_reports。
7. 确认本轮不会运行任何逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：扩展 validator

在 `reverse_agent/project_state.py` 中扩展 `validate_pytest_result_for_report(pytest_text, report_summary)`。

新增行为：

```text
1. 从 report_summary.tests_ran 读取报告声明的命令列表。
2. 从 pytest_result_summary.tests_ran 读取 header 记录的命令列表。
3. 如果 report_summary.tests_ran 是非空 list，则检查每条 report test 是否都出现在 pytest_result_summary.tests_ran 中。
4. 若缺失，返回 warning 或 error：pytest_result tests_ran does not cover codex_report_summary.tests_ran。
5. 返回字段中增加：
   - report_tests_ran_count
   - pytest_result_tests_ran_count
   - tests_ran_covers_report
   - missing_report_tests
6. 对 legacy 无 header 文件保持兼容：tests_ran_covers_report = "unknown"。
7. 对 report_summary.tests_ran 缺失或非 list 的情况不要崩溃，返回 unknown 或 warning。
```

建议规则：

```text
- decision_id mismatch：仍然是 error。
- tests_ran 未覆盖：先作为 warning，不要让 lint-report 硬失败，避免过度破坏旧流程。
- 如果 report_status=SUCCESS 且 tests_ran 完全缺失，则沿用已有 SUCCESS requires non-empty tests_ran 规则。
```

### Phase B：status / lint-report 输出

更新 `status_summary()` 和 `_print_status()`，至少输出：

```text
pytest_result_tests_ran_count
report_tests_ran_count
pytest_result_tests_cover_report
pytest_result_missing_report_tests
```

更新 `lint_report()` 和 `_print_lint_report()`，至少返回/输出：

```text
pytest_result_tests_ran_count
report_tests_ran_count
pytest_result_tests_cover_report
pytest_result_missing_report_tests
```

要求：

```text
1. 如果缺少 report tests，lint-report 应有 warning。
2. 若完全覆盖，lint-report 不应新增 warning。
3. 不改变现有 round_id mismatch / round_manifest missing warning 的语义。
```

### Phase C：更新 active pytest_result.txt

重写 `project_state/pytest_result.txt`，使 `pytest_result_summary.tests_ran` 包含本轮报告声明的全部验证命令。

本轮 Codex 执行完成后，active `pytest_result.txt` 应对应新的 decision：

```text
decision_id = decision_20260523_engineering_pytest_tests_ran_consistency
report_id = report_20260523_engineering_pytest_tests_ran_consistency
round_id = round_20260523_engineering_pytest_tests_ran_consistency
```

并在 header 的 tests_ran 中记录本轮真实运行命令。不要保留任何上一轮逆向 runtime 内容。

### Phase D：测试

更新 `tests/test_project_state.py`，覆盖：

```text
1. pytest_result_summary.tests_ran 完全覆盖 codex_report_summary.tests_ran：tests_ran_covers_report=True。
2. pytest_result_summary.tests_ran 缺少一条 report test：tests_ran_covers_report=False，并列出 missing_report_tests。
3. lint-report 对 tests_ran 缺失覆盖给 warning，不崩溃。
4. status_summary 暴露 tests_ran coverage 字段。
5. legacy 无 header 文件返回 tests_ran_covers_report="unknown"。
6. report_summary.tests_ran 缺失或非 list 时不崩溃。
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py -k "pytest_result or report"
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
1. 当前 codex_execution_report.md 缺失 codex_report_summary。
2. 当前 pytest_result.txt 缺失 pytest_result_summary，且 parser 已经无法兼容 legacy。
3. 为了 tests_ran 覆盖检查需要大规模重写 project_state.py。
4. status/lint-report 接入会导致大量旧测试失败，超过小步兼容范围。
5. 需要读取完整 solve_reports 才能继续。
6. 需要运行逆向 runtime probe 才能构造测试。
7. 本轮 diff 超过 400 行，且主要不是 tests/test_project_state.py。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，字段要求：

```text
report_id = report_20260523_engineering_pytest_tests_ran_consistency
round_id = round_20260523_engineering_pytest_tests_ran_consistency
based_on_decision_id = decision_20260523_engineering_pytest_tests_ran_consistency
status = SUCCESS / PARTIAL / FAILED / BLOCKED
tests_ran = 真实运行命令列表
generated_artifacts = 本轮更新的 project_state 文件列表
```

报告正文必须明确记录：

```text
1. 修改前 pytest_result_summary.tests_ran 缺少哪些 report tests。
2. 是否实现 tests_ran 覆盖校验。
3. status / lint-report 是否输出 coverage 字段。
4. active pytest_result.txt 是否已覆盖本轮真实 tests_ran。
5. 是否没有运行任何逆向 runtime probe。
6. 真实测试命令和结果。
7. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- pytest_result_summary.tests_ran 覆盖 codex_report_summary.tests_ran。
- validator 能识别 missing report tests。
- status / lint-report 能显示 tests_ran coverage 状态。
- legacy 无 header 文件兼容，不崩溃。
- tests/test_project_state.py 相关测试通过。
- 未运行任何逆向 runtime probe。
- diff 控制在 400 行内。

ACCEPTED_WITH_LIMITATIONS：
- coverage 校验完成，但 tests_ran 缺失只作为 warning，不作为 error。
- round_id mismatch / round_manifest missing 仍存在，但未扩大。

REWORK_REQUIRED：
- pytest_result_summary.tests_ran 继续缺少当前 report tests 且未被 validator 报告。
- decision_id mismatch 仍被当成可信。
- 删除 active project_state 文件。
- 运行了逆向 runtime probe。
- 缺少测试或测试记录无法对应当前 decision。

BLOCKED：
- 当前 report/pytest header 缺失且无法建立兼容解析路径。
- 仓库内无法实现 tests_ran coverage 校验。
```

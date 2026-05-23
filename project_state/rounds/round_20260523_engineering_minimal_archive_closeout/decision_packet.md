```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_minimal_archive_closeout",
  "round_id": "round_20260523_engineering_minimal_archive_closeout",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

上一轮工程审计结论是 `ACCEPTED_WITH_LIMITATIONS`：round 关系已经建模清楚，`decision.round_id == report.round_id` 会被显式检查，工程协作 round 与 sample `current_state.round_id` 不一致会被表达为 `different_but_allowed_sample_state`；但当前 active report 仍未归档，`lint-report` 仍有预期 warning：`report round not archived yet`，`archive_status=not_archived`。

本轮只解决工程支线 closeout 语义：定义并验证一个安全的 minimal archive 结束步骤，使完成当前工程 round 后可以进入 `archive_status=archived`，同时不重新引入 `git_diff.patch` / full state snapshot 污染。

## 1. Goal

本轮目标：

```text
1. 定义工程支线 round 的 closeout 规则：
   - Codex 在完成 active codex_execution_report.md 和 pytest_result.txt 后，允许执行一次默认 minimal archive-round。
   - minimal archive 只允许归档 decision_packet.md、codex_execution_report.md、pytest_result.txt、round_manifest.json。
   - 不允许默认生成 git_diff.patch。
   - 不允许默认复制 current_state.json / artifact_index.json / negative_results.json / model_gate.json / task_packet.json。
2. 增加或调整 project_state 侧校验，让 lint-report 能区分：
   - archive_status=not_archived：当前 report 尚未 closeout。
   - archive_status=archived：当前 report round 已存在 minimal round_manifest。
   - archive_status=non_minimal 或 polluted：manifest 包含禁止的 diff/state snapshot 文件。
3. 如果 round_manifest 存在但包含 git_diff.patch 或 full state snapshot，lint-report 必须 warning 或 error。
4. 给出明确 closeout 操作方式：
   python -m reverse_agent.project_state archive-round --state-dir project_state --round-id <current_report_round_id>
   且不得带 --include-diff / --include-state-snapshot。
5. 更新 tests/test_project_state.py，覆盖 minimal archive accepted、not archived warning、polluted archive rejected/warned。
6. 本轮 Codex 完成后，应让 active lint-report 对当前 round 至少达到：
   - report_decision_round_id_match=True
   - report_current_state_round_relation=different_but_allowed_sample_state 或 same
   - archive_status=archived，或如果未执行 archive，则必须在 report 中解释为什么只达到 ACCEPTED_WITH_LIMITATIONS。
```

本轮重点是 closeout policy 和 minimal archive gate，不是历史 round 清理。

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

`task_packet.json` 仍来自 `samplereverse` 样本状态，`task_packet.task` / `derived_task` 是逆向主线派生建议，不是本轮工程任务。`task_packet.execution_scope` 为 `decision_packet_controls_current_round`，因此本轮 Codex 实际执行权威是 `project_state/decision_packet.md`。

当前 `current_state.json` 是 sample evidence state：

```text
state_scope = sample_state
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
```

这不应被改成工程协作 round。

上一轮有效报告：

```text
report_id = report_20260523_engineering_round_manifest_consistency
round_id = round_20260523_engineering_round_manifest_consistency
based_on_decision_id = decision_20260523_engineering_round_manifest_consistency
status = SUCCESS
```

上一轮 active `pytest_result.txt` 显示：

```text
report_decision_round_id_match=True
report_current_state_round_relation=different_but_allowed_sample_state
round_manifest_present=False
archive_status=not_archived
pytest_result_tests_cover_report=True
```

上一轮 `lint-report` 已经从旧 warning：

```text
report round_id does not match current_state.round_id
round_manifest missing
```

收敛为：

```text
report round not archived yet
archive_status=not_archived
```

这说明 round relation 已完成，但 closeout archive 尚未完成。

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
不要运行 archive-round --include-diff。
不要运行 archive-round --include-state-snapshot。
不要把 git_diff.patch 或 full state snapshot 重新纳入默认 round archive。
不要引入数据库、调度平台、外部服务或重型依赖。
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
.gitignore
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
3. 读取当前 pytest_result_summary.round_id。
4. 运行或检查 lint-report 当前输出，确认 archive_status=not_archived 与 warning=report round not archived yet。
5. 检查 archive_round 默认文件集合，确认默认不包含 git_diff.patch 或 full state snapshot。
6. 检查 round_manifest 的 files 结构，确认 lint-report 能判断是否 minimal archive。
7. 检查 .gitignore 是否仍忽略 project_state/rounds/*/git_diff.patch 和 full state snapshot。
8. 确认本轮不需要读取 solve_reports。
9. 确认本轮不会运行任何逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：定义 minimal archive 判定

在 `reverse_agent/project_state.py` 中扩展 round manifest 检查逻辑。

建议增加 helper，名称可按现有风格决定，例如：

```text
classify_round_archive(manifest: dict) -> dict
```

最低输出字段：

```text
archive_status: "archived" | "not_archived" | "non_minimal" | "polluted" | "unknown"
round_manifest_present: bool
round_manifest_files: list[str]
round_manifest_forbidden_files: list[str]
round_manifest_required_files_missing: list[str]
round_manifest_warning: str
```

允许的 minimal archive 文件：

```text
decision_packet.md
codex_execution_report.md
pytest_result.txt
round_manifest.json
```

禁止默认出现的文件：

```text
git_diff.patch
artifact_index.json
current_state.json
negative_results.json
model_gate.json
task_packet.json
```

语义要求：

```text
1. manifest 不存在：archive_status=not_archived，warning=report round not archived yet。
2. manifest 存在且只包含 minimal allowed files，并包含 codex_execution_report.md / pytest_result.txt：archive_status=archived。
3. manifest 存在但缺少 codex_execution_report.md 或 pytest_result.txt：warning。
4. manifest 存在且包含 git_diff.patch：至少 warning，建议 error 或 archive_status=polluted。
5. manifest 存在且包含 full state snapshot：至少 warning，建议 archive_status=non_minimal。
6. 不要自动删除或修复历史 manifest。
```

### Phase B：lint-report / status 输出

更新 `status_summary()` / `_print_status()` 和 `lint_report()` / `_print_lint_report()`，输出：

```text
archive_status
round_manifest_present
round_manifest_path
round_manifest_files
round_manifest_forbidden_files
round_manifest_required_files_missing
```

要求：

```text
1. minimal archived 时，不再输出 report round not archived yet。
2. polluted/non_minimal archive 时，lint-report 能明确暴露 forbidden files。
3. 不改变上一轮已完成的 report_decision_round_id_match / report_current_state_round_relation 语义。
```

### Phase C：closeout 执行规则

Codex 完成本轮代码和测试后，可以执行一次：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_minimal_archive_closeout
```

严格禁止：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_minimal_archive_closeout --include-diff
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_minimal_archive_closeout --include-state-snapshot
```

注意 closeout 顺序：

```text
1. 先完成代码和 tests/test_project_state.py。
2. 写入 active project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
3. 运行 status / lint-report，确认除 archive_status 外逻辑正确。
4. 最后运行默认 minimal archive-round。
5. 再运行 status / lint-report，确认 archive_status=archived。
6. archive-round 之后不要再修改 active decision/report/pytest，除非重新 archive 当前 round。
```

如果因为 archive-round 幂等或报告更新顺序无法保证最终 archived 状态，Codex 必须停止并报告，不要强行反复覆盖 round 目录。

### Phase D：测试

更新 `tests/test_project_state.py`，覆盖：

```text
1. manifest 不存在：archive_status=not_archived，warning=report round not archived yet。
2. minimal manifest 存在且包含 codex_execution_report.md / pytest_result.txt：archive_status=archived，无 not_archived warning。
3. manifest 包含 git_diff.patch：archive_status=polluted 或 warning/error 含 forbidden file。
4. manifest 包含 current_state.json / artifact_index.json 等 full snapshot：archive_status=non_minimal 或 warning 含 forbidden file。
5. status_summary 输出 round_manifest_files / forbidden / missing 字段。
6. lint-report 对 default minimal archive 通过。
7. archive_round 默认生成的 manifest 能被 classify 为 archived/minimal。
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py -k "archive or manifest or lint_report or status"
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果执行 closeout archive-round，额外运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_minimal_archive_closeout
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
3. archive_round 默认仍会生成 git_diff.patch 或 full state snapshot。
4. 需要改写 current_state.round_id 才能让 lint-report 通过。
5. 需要自动执行 --include-diff 或 --include-state-snapshot 才能继续。
6. 需要删除历史 round 目录或执行 git rm --cached 才能继续。
7. 需要读取完整 solve_reports 才能继续。
8. 需要运行逆向 runtime probe 才能构造测试。
9. 为了 closeout 需要大规模重写 project_state.py。
10. 本轮 diff 超过 500 行，且主要不是 tests/test_project_state.py 或 minimal archive manifest。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，字段要求：

```text
report_id = report_20260523_engineering_minimal_archive_closeout
round_id = round_20260523_engineering_minimal_archive_closeout
based_on_decision_id = decision_20260523_engineering_minimal_archive_closeout
status = SUCCESS / PARTIAL / FAILED / BLOCKED
tests_ran = 真实运行命令列表
generated_artifacts = 本轮更新的 project_state 文件列表，包括 minimal round files（如果已 closeout）
```

报告正文必须明确记录：

```text
1. 修改前 archive_status 是什么。
2. archive_round 默认归档文件集合是否 minimal。
3. 是否实现 forbidden files 检查。
4. 是否执行了 default minimal archive-round。
5. 当前 active status/lint-report 的 archive_status。
6. 如果 archive_status 仍是 not_archived，为什么只能 ACCEPTED_WITH_LIMITATIONS。
7. 是否没有运行任何逆向 runtime probe。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- default archive-round 仍是 minimal，不包含 git_diff.patch/full state snapshot。
- lint-report 能识别 archived / not_archived / polluted 或 non_minimal。
- 当前 active round 已通过 default minimal archive closeout，archive_status=archived。
- status / lint-report 输出 forbidden files 和 required missing files。
- tests/test_project_state.py 相关测试通过。
- 未运行任何逆向 runtime probe。
- diff 控制在 500 行内。

ACCEPTED_WITH_LIMITATIONS：
- minimal archive 判定和污染检查完成，但由于 archive-round 顺序或环境原因，当前 active round 仍是 archive_status=not_archived。

REWORK_REQUIRED：
- archive-round 默认重新生成 git_diff.patch。
- archive-round 默认重新归档 full state snapshot。
- polluted archive 被 lint-report 当成 clean archived。
- 为消除 warning 修改了 current_state.round_id。
- 自动创建大量 round 文件或处理历史大文件。
- 运行了逆向 runtime probe。
- 缺少测试或测试记录无法对应当前 decision。

BLOCKED：
- 当前 report/decision meta 缺失，无法建立 closeout round。
- 仓库内无法区分 minimal archive 与 polluted archive。
```

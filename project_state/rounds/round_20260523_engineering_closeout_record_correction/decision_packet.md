```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_engineering_closeout_record_correction",
  "round_id": "round_20260523_engineering_closeout_record_correction",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮属于工程架构改造支线，不推进 `samplereverse` 逆向解题主线。

上一轮审计结论是 `ACCEPTED_WITH_LIMITATIONS`：minimal archive closeout 的核心代码和 round manifest 基本成立，但 active `codex_execution_report.md` / `pytest_result.txt` 以及已归档副本中仍把最后的 `archive-round` / post-archive `status` / post-archive `lint-report` 结果写成 `pending`，同时又在 `tests_ran` 中声明这些命令已经运行。这是记录可信性问题，不是继续扩展架构的问题。

本轮只做 closeout record correction：验证当前 minimal archive 状态，修正 active report/result 的自相矛盾记录，必要时补一个极小的文本级或 lint 级防回归检查。除非当前 `status` / `lint-report` 实际失败，否则不要修改核心逻辑。

## 1. Goal

本轮目标：

```text
1. 重新核对当前 active decision/report/pytest/round_manifest 状态。
2. 验证上一轮 minimal archive closeout 是否已经实际满足：
   - report_decision_round_id_match=True
   - report_current_state_round_relation=different_but_allowed_sample_state 或 same
   - round_manifest_present=True
   - archive_status=archived
   - round_manifest_forbidden_files=[]
   - round_manifest_required_files_missing=[]
3. 修正 active project_state/codex_execution_report.md 和 project_state/pytest_result.txt：
   - 不允许出现 pending final closeout command。
   - 不允许出现 pending final post-archive verification。
   - `tests_ran` 只能列出有明确结果的真实命令。
   - 若某命令是在 report 写入之后才执行，不能在该 report 的 `tests_ran` 中声称它已有结果。
4. 如果需要归档本 correction round，只允许默认 minimal archive：
   python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_closeout_record_correction
   不得带 --include-diff 或 --include-state-snapshot。
5. 如果发现当前 `lint-report` 已能识别 `archive_status=archived`，本轮不要改 `reverse_agent/project_state.py`。
6. 如果发现 `lint-report` 无法识别现有 clean minimal manifest，才允许做最小代码修复，并必须补测试。
```

本轮结束后，active report/result 必须是自洽的：不能一边声明 `SUCCESS/ACCEPTED`，一边把关键验证写成 `pending`。

## 2. Current Evidence

当前任务主线判断：工程架构改造支线。

`task_packet.json` 仍来自 `samplereverse` 样本状态，`task_packet.task` / `derived_task` 是逆向主线派生建议，不是本轮工程任务。`task_packet.execution_scope` 为 `decision_packet_controls_current_round`，因此本轮 Codex 实际执行权威是 `project_state/decision_packet.md`。

当前 `current_state.json` 仍是 sample evidence state：

```text
state_scope = sample_state
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
```

这不应被改成工程协作 round。

上一轮 active report 元信息：

```text
report_id = report_20260523_engineering_minimal_archive_closeout
round_id = round_20260523_engineering_minimal_archive_closeout
based_on_decision_id = decision_20260523_engineering_minimal_archive_closeout
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

上一轮 round manifest 已存在：

```text
project_state/rounds/round_20260523_engineering_minimal_archive_closeout/round_manifest.json
archive_mode = minimal
included_diff = false
included_state_snapshot = false
files = codex_execution_report.md, decision_packet.md, pytest_result.txt
omitted_files = artifact_index.json, current_state.json, negative_results.json, model_gate.json, task_packet.json, git_diff.patch
```

上一轮审计发现的限制：

```text
1. codex_report_summary.tests_ran 声称运行了 archive-round / status / lint-report。
2. report 正文 Verification 表却把这些步骤写成 pending。
3. pytest_result_summary.tests_ran 也列出了这些命令。
4. pytest_result 正文同样写 pending。
5. 已归档 report/pytest 副本中也保留了 pending 文本。
```

artifact freshness 说明：

```text
本轮不依赖 solve_reports 逆向 artifact。
artifact_index.latest_artifacts_v2 中 stale/missing 的逆向 artifact 不应触发 runtime probe。
不要因为 current_state 的 sample round 较旧就重跑逆向 harness。
```

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 逆向 sidecar。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何逆向 runtime probe。
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
不要为了修正文本记录而大改 project_state.py。
不要在 tests_ran 中列出没有明确结果的 pending 命令。
不要让本轮 diff 超过 200 行；若超过，停止并报告原因。
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
project_state/rounds/round_20260523_engineering_minimal_archive_closeout/round_manifest.json
project_state/rounds/round_20260523_engineering_minimal_archive_closeout/codex_execution_report.md
project_state/rounds/round_20260523_engineering_minimal_archive_closeout/pytest_result.txt
```

必要时检查：

```text
reverse_agent/project_state.py
tests/test_project_state.py
.gitignore
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
1. 读取当前 decision_meta，确认本轮 decision_id 是 decision_20260523_engineering_closeout_record_correction。
2. 读取当前 active codex_report_summary，确认它对应上一轮 minimal_archive_closeout。
3. 读取当前 active pytest_result_summary，确认其中存在 pending 记录问题。
4. 读取上一轮 round_manifest，确认：
   - archive_mode=minimal
   - included_diff=false
   - included_state_snapshot=false
   - files 只包含 decision_packet.md / codex_execution_report.md / pytest_result.txt
5. 运行：
   python -m reverse_agent.project_state status --state-dir project_state
6. 运行：
   python -m reverse_agent.project_state lint-report --state-dir project_state
7. 如果上述命令显示 archive_status=archived 且 lint-report OK，则本轮不得修改核心代码。
8. 确认本轮不需要读取 solve_reports。
9. 确认本轮不会运行任何逆向 runtime probe。
```

## 6. Implementation Scope

### Phase A：验证当前 closeout 状态

先只运行状态命令，不改代码：

```bash
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果输出显示：

```text
archive_status=archived
round_manifest_forbidden_files=[]
round_manifest_required_files_missing=[]
report_decision_round_id_match=True
```

则进入 Phase B，不允许改 `reverse_agent/project_state.py`。

如果输出不是上述状态，则停止并报告实际错误；只有在确认是 closeout 判定逻辑 bug 时，才允许最小修改 `reverse_agent/project_state.py` 和 `tests/test_project_state.py`。

### Phase B：修正 active report/result 记录

更新 `project_state/codex_execution_report.md`，要求：

```text
1. 顶部 codex_report_summary：
   report_id = report_20260523_engineering_closeout_record_correction
   round_id = round_20260523_engineering_closeout_record_correction
   based_on_decision_id = decision_20260523_engineering_closeout_record_correction
   status = SUCCESS / PARTIAL / FAILED / BLOCKED
2. tests_ran 只列出本轮真实运行且有明确结果的命令。
3. 不允许把 pending 命令列入 tests_ran。
4. 正文必须明确写：
   - 上一轮 minimal_archive_closeout 的 manifest 是否 clean。
   - 当前 status/lint-report 的实际输出摘要。
   - 是否修改了核心代码。
   - 是否没有运行逆向 runtime probe。
```

更新 `project_state/pytest_result.txt`，要求：

```text
1. 顶部 pytest_result_summary 必须对应本轮 decision/report/round。
2. tests_ran 必须覆盖 codex_report_summary.tests_ran。
3. 每条命令必须有明确 result，不能写 pending。
```

### Phase C：归档 correction round（可选但推荐）

完成 active report/result 后，可执行一次默认 minimal archive：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_closeout_record_correction
```

要求：

```text
1. 不得带 --include-diff。
2. 不得带 --include-state-snapshot。
3. 如果 archive-round 成功，generated_artifacts 可列出新 round 的 decision/report/pytest/manifest。
4. 不要在 report 中声称执行了 post-archive status/lint-report，除非确实执行并且不会再改写该 report。
5. 如果 archive-round 因 manifest 已存在且 differs 而失败，停止并报告，不要强行覆盖。
```

### Phase D：仅在必要时补小型防回归

如果 Codex 判断需要防止后续报告再次出现 pending 命令，可在 `tests/test_project_state.py` 中增加一个很小的测试或 helper，但仅限以下范围：

```text
- 检查 codex_report_summary.tests_ran 与 pytest_result_summary.tests_ran 的覆盖关系。
- 或检查 pytest_result 正文中不要把 tests_ran 中的命令标记为 pending。
```

如果实现这一步导致 diff 超过 200 行，停止并报告。

## 7. Tests

必须运行：

```bash
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

如果修改了 `reverse_agent/project_state.py` 或 `tests/test_project_state.py`，还必须运行：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py -k "archive or manifest or lint_report or status or pytest_result"
python -m pytest -q tests/test_project_state.py
```

如果执行 correction round 归档，运行：

```bash
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_engineering_closeout_record_correction
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
3. 当前 pytest_result.txt 缺失 pytest_result_summary。
4. status 或 lint-report 显示当前 minimal_archive_closeout 并非 archived，且原因不是记录文本问题。
5. round_manifest 中发现 git_diff.patch 或 full state snapshot。
6. 需要改写 current_state.round_id 才能让 lint-report 通过。
7. 需要执行 --include-diff 或 --include-state-snapshot 才能继续。
8. 需要删除历史 round 目录或执行 git rm --cached 才能继续。
9. 需要读取完整 solve_reports 才能继续。
10. 需要运行逆向 runtime probe 才能继续。
11. 为了修正 pending 记录需要大规模重写 project_state.py。
12. 本轮 diff 超过 200 行，且主要不是 report/pytest 文本修正或极小测试补充。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含 `codex_report_summary`，字段要求：

```text
report_id = report_20260523_engineering_closeout_record_correction
round_id = round_20260523_engineering_closeout_record_correction
based_on_decision_id = decision_20260523_engineering_closeout_record_correction
status = SUCCESS / PARTIAL / FAILED / BLOCKED
acceptance_recommendation = ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED
files_changed = 真实修改文件列表
tests_ran = 真实运行且有明确结果的命令列表
generated_artifacts = 本轮更新或生成的 project_state 文件列表
```

报告正文必须明确记录：

```text
1. 上一轮 pending 矛盾是否已消除。
2. 当前 status/lint-report 的真实结果。
3. 当前 archive_status。
4. 当前 round_manifest_forbidden_files。
5. 当前 round_manifest_required_files_missing。
6. 是否修改了核心代码。
7. 是否没有运行任何逆向 runtime probe。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- active report/pytest 不再包含 pending final closeout / pending final post-archive verification。
- tests_ran 中每条命令都有明确结果。
- status/lint-report 真实运行并记录。
- 已确认上一轮 minimal archive 是 clean archived，或本轮 correction round 也已 clean minimal archived。
- 未修改 current_state.round_id。
- 未归档 git_diff.patch/full state snapshot。
- 未运行任何逆向 runtime probe。

ACCEPTED_WITH_LIMITATIONS：
- active report/pytest 已自洽，但 correction round 未归档；报告必须解释原因。

REWORK_REQUIRED：
- 仍有 pending 命令被列入 tests_ran。
- report/pytest 的 decision_id/report_id/round_id 不匹配。
- 把 polluted/non_minimal archive 当成 clean archived。
- 为消除 warning 修改 current_state.round_id。
- 默认归档了 git_diff.patch 或 full state snapshot。
- 运行了逆向 runtime probe。

BLOCKED：
- 当前 active meta 缺失，无法建立 correction round。
- 当前 project_state 状态命令无法运行，且不是本轮可修复的记录问题。
```

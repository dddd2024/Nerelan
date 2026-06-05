```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_static_triage_metadata_rework_v1",
  "round_id": "round_20260605_cpp1_static_triage_metadata_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **tool_integration**。

上一轮 `decision_20260605_cpp1_2f6fcb63_static_triage_v1` 审计结论为 `REWORK_REQUIRED`。核心 static triage artifact 已经有价值，但存在元数据和测试记录缺口：

```text
1. decision_packet.round_id 是 round_20260605_cpp1_2f6fcb63_static_triage_v1。
2. codex_execution_report.round_id / pytest_result round_id / artifact_index.source_run 使用了 round_20260605_cpp1_single_sample_static_triage_v1。
3. required command 缺失：python -m py_compile reverse_agent/tool_runners.py。
4. codex_report_summary.tests_ran 中 CLI 命令用了省略号，不是完整可复现命令。
5. pytest_result 中 CLI 命令缺少 --artifact-index project_state/artifact_index.json。
```

本轮目标：**只修复 cpp1_2f6fcb63 static triage 的 metadata consistency 和 required test 记录缺口**。

除非重新运行暴露真实错误，否则不得修改 static triage 核心逻辑。

必须保持：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json:
  sample_id=cpp1_2f6fcb63
  executed_sample=false
  static_only=true
  runtime_validated=false
  candidate=null
  known_candidate=""
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已完成且应保持的有效事实：

```text
reverse_agent/local_reverse_single_sample_static_triage.py exists.
tests/test_local_reverse_single_sample_static_triage.py exists.
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json exists.
artifact tool_status=success.
artifact source_tool=IDA.
artifact triage includes interesting strings, functions, one compare_context, validation_function_candidates, solver_profile_hypotheses, and decompiler snippets.
_main_0 pseudocode indicates scanf("%s", Str), length check, byte transform, and compare against byte_429A30.
No candidate or known_candidate was generated.
No solved status update was performed.
```

Current defects to fix:

```text
codex_execution_report.md:
  report_id=report_20260605_cpp1_single_sample_static_triage_v1
  round_id=round_20260605_cpp1_single_sample_static_triage_v1
  based_on_decision_id is correct but round_id does not match previous decision round.

pytest_result.txt:
  Round=round_20260605_cpp1_single_sample_static_triage_v1
  CLI command lacks --artifact-index project_state/artifact_index.json.

artifact_index.json:
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.source_run=round_20260605_cpp1_single_sample_static_triage_v1
```

This rework must create a new aligned round:

```text
decision_id=decision_20260605_cpp1_static_triage_metadata_rework_v1
round_id=round_20260605_cpp1_static_triage_metadata_rework_v1
report_id=report_20260605_cpp1_static_triage_metadata_rework_v1
artifact_index.latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.source_run=round_20260605_cpp1_static_triage_metadata_rework_v1
```

`negative_results.json` still forbids old blind search, only increasing search budget, committing full solve_reports, and repeating old dynamic-probe directions. This rework must not enter those directions.

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行本地样本。
2. 不做动态探测或交互式调试。
3. 不运行旧盲搜 solver。
4. 不生成 candidate、flag、known_candidate。
5. 不把 cpp1_2f6fcb63 标记 solved。
6. 不提交原始样本文件。
7. 不提交 full solve_reports、IDA 数据库副产物或无必要日志。
8. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
9. 不修改 .codex-skills。
10. 不新建第二套静态分析工具接口。
11. 不重构 reverse_agent/local_reverse_single_sample_static_triage.py。
12. 不把静态证据说成 runtime validation。
```

允许：

```text
1. 重新运行 required tests。
2. 重新运行 single-sample static triage CLI，命令必须完整记录。
3. 重新生成 project_state/local_reverse_cpp1_2f6fcb63_static_triage.json。
4. 更新 artifact_index.json 中 local_reverse_cpp1_2f6fcb63_static_triage 的 sha256、size_bytes、modified_at、source_run。
5. 更新 codex_execution_report.md 与 pytest_result.txt。
6. 仅当 required tests 暴露真实错误时，才允许最小修复相关代码或测试。
```

---

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

必须检查：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
project_state/local_reverse_evaluation_queue.json
project_state/local_reverse_inventory.json
```

允许修改：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅当重新运行发现真实问题时，才允许最小修改：

```text
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是 advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮只是 metadata/test-record rework。
5. 是否确认目标 artifact 仍是 cpp1_2f6fcb63 static triage。
6. 是否补跑 python -m py_compile reverse_agent/tool_runners.py。
7. 是否补跑 python -m py_compile reverse_agent/local_reverse_single_sample_static_triage.py。
8. 是否运行 tests/test_local_reverse_single_sample_static_triage.py。
9. 是否运行 tests/test_project_state.py。
10. 是否运行 lint-decision 与 lint-report。
11. 是否使用完整 CLI 命令，并包含 --artifact-index project_state/artifact_index.json。
12. 是否确认 report_id、round_id、decision_id 对齐当前 decision。
13. 是否确认 artifact_index source_run 等于 round_20260605_cpp1_static_triage_metadata_rework_v1。
14. 是否确认 artifact_index sha256 与实际 artifact 文件一致。
15. 是否确认 artifact 仍为 executed_sample=false / static_only=true / runtime_validated=false。
16. 是否确认 artifact 仍为 candidate=null / known_candidate=""。
17. 是否没有动态执行样本。
18. 是否没有运行 solver。
19. 是否没有提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 修改。
20. codex_report_summary.tests_ran 是否完整列出 required commands，且无省略号。
21. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选路径：不改核心代码，只重新运行并同步记录。

必须保持 artifact 语义：

```text
sample_id=cpp1_2f6fcb63
analysis_mode=single_sample_static_triage
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
tool_status=success 或 blocked
candidate=null
known_candidate=""
```

必须同步：

```text
codex_execution_report.md:
  report_id=report_20260605_cpp1_static_triage_metadata_rework_v1
  round_id=round_20260605_cpp1_static_triage_metadata_rework_v1
  based_on_decision_id=decision_20260605_cpp1_static_triage_metadata_rework_v1
  status=SUCCESS only if all required commands pass

pytest_result.txt:
  Round=round_20260605_cpp1_static_triage_metadata_rework_v1
  Decision=decision_20260605_cpp1_static_triage_metadata_rework_v1
  Report=report_20260605_cpp1_static_triage_metadata_rework_v1

artifact_index.json:
  latest_artifacts.local_reverse_cpp1_2f6fcb63_static_triage=project_state\\local_reverse_cpp1_2f6fcb63_static_triage.json
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.freshness=current
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.source_run=round_20260605_cpp1_static_triage_metadata_rework_v1
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.sha256=<actual file sha256>
  latest_artifacts_v2.local_reverse_cpp1_2f6fcb63_static_triage.size_bytes=<actual file size>
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/tool_runners.py
python -m py_compile reverse_agent/local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_local_reverse_single_sample_static_triage.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id cpp1_2f6fcb63 --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --artifact-index project_state/artifact_index.json --out project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
git diff --check
git status --short
```

测试期望：

```text
1. 所有 required commands Exit Code 0。
2. tests_ran 不使用省略号。
3. CLI command 完整记录，并包含 --artifact-index。
4. lint-report 显示 report/decision/round 对齐当前 rework decision。
5. artifact_index source_run 与当前 round_id 一致。
6. artifact 仍不生成 candidate/known_candidate。
7. git status --short 不出现原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法补跑 py_compile reverse_agent/tool_runners.py。
2. 无法让 report/decision/pytest round_id 对齐。
3. 无法让 artifact_index source_run 与当前 round_id 对齐。
4. 重新生成 artifact 导致 candidate/known_candidate 出现。
5. 需要动态执行样本才能完成。
6. 需要运行 solver 才能完成。
7. 需要提交原始样本、full solve_reports、IDA 数据库副产物或 .codex-skills 才能完成。
```

完成条件：

```text
1. codex_execution_report.md、pytest_result.txt、decision_packet.md 的 decision_id/round_id 对齐。
2. artifact_index 中 local_reverse_cpp1_2f6fcb63_static_triage.source_run 等于当前 round_id。
3. required commands 全部记录且通过。
4. CLI 命令完整记录，无省略号，包含 --artifact-index。
5. artifact 仍为 static-only triage，不含 candidate/flag/known_candidate。
6. git status --short 不出现禁止文件。
```

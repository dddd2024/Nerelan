```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_reextract_test_record_rework_v1",
  "round_id": "round_20260605_affine_reextract_test_record_rework_v1",
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

上一轮 `decision_20260605_affine_reextract_scope_rework_v1` 已完成主要功能返工，但审计结论为 `REWORK_REQUIRED`，原因是 `pytest_result.txt` 缺少两个 required command 的真实记录：

```text
1. git diff --check
2. git status --short
```

本轮目标：**只做测试记录返工，补齐 `git diff --check` 和 `git status --short` 的真实执行记录，并更新 `codex_execution_report.md` 与 `pytest_result.txt`。**

不得改业务逻辑，不得重新扩大实现范围。

必须完成：

```text
1. 读取 project_state/decision_packet.md、codex_execution_report.md、pytest_result.txt、artifact_index.json。
2. 确认 task_packet.task 只是 advisory，本 decision_packet 是本轮唯一执行权威。
3. 确认 reverse_agent/local_reverse_affine_main_input_flow_reextract.py 仍不存在。
4. 确认 reverse_agent/local_reverse_targeted_static_reextract.py 已支持 affine-main-input-flow，不要做功能改动。
5. 运行并记录所有 required tests，包括 git diff --check 和 git status --short。
6. 更新 project_state/pytest_result.txt，使其记录所有命令、Exit code 和输出摘要。
7. 更新 project_state/codex_execution_report.md，使 codex_report_summary.based_on_decision_id 等于 decision_20260605_affine_reextract_test_record_rework_v1。
```

---

## 2. Current Evidence

上一轮功能返工已基本完成：

```text
reverse_agent/local_reverse_affine_main_input_flow_reextract.py 已删除。
reverse_agent/local_reverse_targeted_static_reextract.py 已支持 affine-main-input-flow。
project_state/local_reverse_affine_main_input_flow_reextract.json 已重新生成。
artifact_index 已将 local_reverse_affine_main_input_flow_reextract 标记为 freshness=current，source_run=round_20260605_affine_reextract_scope_rework_v1。
```

唯一阻断项：

```text
pytest_result.txt 缺少 git diff --check 和 git status --short 的执行记录。
```

当前必须保留的事实：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
executed_sample: false
analysis remains static JSON processing only
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不重新运行 IDA。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新增 parser、runner、solver。
11. 不重新引入 reverse_agent/local_reverse_affine_main_input_flow_reextract.py。
12. 不修改 reverse_agent/local_reverse_targeted_static_reextract.py，除非测试暴露语法或格式问题；如必须修改，必须在报告中说明原因。
13. 不改 artifact_index，除非发现上一轮 source_run/freshness 回退或记录错误。
14. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
```

允许：

```text
1. 运行测试和状态检查命令。
2. 更新 project_state/pytest_result.txt。
3. 更新 project_state/codex_execution_report.md。
4. 仅在测试失败且必须修复时，做最小必要修复。
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
project_state/local_reverse_affine_main_input_flow_reextract.json
reverse_agent/local_reverse_targeted_static_reextract.py
```

必须确认不存在：

```text
reverse_agent/local_reverse_affine_main_input_flow_reextract.py
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
3. 是否没有修改业务逻辑。
4. 是否确认 reverse_agent/local_reverse_affine_main_input_flow_reextract.py 仍不存在。
5. 是否确认 reverse_agent/local_reverse_targeted_static_reextract.py 仍支持 affine-main-input-flow。
6. 是否确认 artifact_index 没有回退。
7. 是否记录 git diff --check，Exit code 0。
8. 是否记录 git status --short，Exit code 0。
9. 是否记录 py_compile、pytest、lint-decision、lint-report、bounded command，且 Exit code 0。
10. 是否没有运行 affine.exe。
11. 是否没有运行 solver、runtime probe、debugger、emulator。
12. 是否没有重新运行 IDA。
13. 是否没有上传原始样本。
14. 是否没有提交 full solve_reports。
15. 是否没有修改 .codex-skills。
16. 是否更新 codex_execution_report.md 和 pytest_result.txt。
17. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_reextract_test_record_rework_v1。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不允许修改：

```text
reverse_agent/local_reverse_targeted_static_reextract.py
project_state/artifact_index.json
project_state/local_reverse_affine_main_input_flow_reextract.json
```

例外：如果 required command 暴露必须修复的问题，允许最小修复，并必须在报告中明确说明：

```text
1. 失败命令；
2. 失败原因；
3. 修改文件；
4. 为什么该修改不扩大任务范围。
```

---

## 7. Tests

必须运行并记录全部命令、Exit code 和输出摘要：

```bash
python -m py_compile reverse_agent/local_reverse_targeted_static_reextract.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.local_reverse_targeted_static_reextract --mode affine-main-input-flow --sample-id affine_8cfebe03 --summary project_state/local_reverse_affine_ida_summary.json --evidence solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json --out project_state/local_reverse_affine_main_input_flow_reextract.json
git diff --check
git status --short
```

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPTED`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 任一 required command 非 0。
2. reverse_agent/local_reverse_affine_main_input_flow_reextract.py 重新出现。
3. artifact_index 回退到 round_20260604_affine_main_input_flow_reextract_v1。
4. 完成本轮需要运行 affine.exe。
5. 完成本轮需要 solver、runtime probe、debugger、emulator。
6. 完成本轮需要重新运行 IDA 或上传原始样本。
7. 完成本轮需要提交 full solve_reports。
```

完成条件：

```text
1. pytest_result.txt 记录 7 个 required commands，包含 git diff --check 和 git status --short。
2. codex_execution_report.md 与 decision_20260605_affine_reextract_test_record_rework_v1 对齐。
3. 没有业务逻辑改动。
4. affine 专用脚本仍不存在。
5. artifact_index 没有回退。
```

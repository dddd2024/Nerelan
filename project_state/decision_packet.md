```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_fix_training_status_overlay_report_lint_v1",
  "round_id": "round_20260604_fix_training_status_overlay_report_lint_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

本轮目标是修复上一轮 `fix_training_status_overlay_audit_v1` 后仍残留的 report/lint 阻断点。上一轮已经修复了 `status_overlay.json` fixture 污染、evaluation queue 的 `0 bytes` 问题和测试输出路径隔离问题；当前剩余问题集中在报告与测试记录对齐。

本轮只修报告和测试记录，不改训练状态业务逻辑，不重新设计 inventory/status/queue，不进入样本求解。

必须完成：

```text
1. 修复 project_state/codex_execution_report.md 中残留旧 decision_id 的正文内容。
2. 确保 codex_report_summary.based_on_decision_id 全文件语义一致为 decision_20260604_fix_training_status_overlay_report_lint_v1。
3. 重新运行 project_state lint-report 并确保 Exit code 0。
4. 更新 project_state/pytest_result.txt，使所有 required commands 都是真实执行且 Exit code 0。
5. codex_execution_report.md 的 status/acceptance_recommendation 必须与 pytest_result.txt 一致。
```

本轮不运行 solver，不运行 IDA/Ghidra，不运行动态分析，不上传原始样本。

---

## 2. Current Evidence

上一轮审计结论仍为 `REWORK_REQUIRED`。

已修复：

```text
1. training_materials/local_reverse/status_overlay.json 已恢复为真实 29 个样本，不再是 todo1/todo.exe fixture。
2. local_reverse_evaluation_queue.json 的 reason 已使用真实 size_bytes，不再全部显示 0 bytes。
3. tests/test_local_reverse_training_status.py 的 test_main_cli_build 已显式传入 --github-status-out tmp_path，避免污染真实仓库产物。
```

仍未修复：

```text
1. project_state/pytest_result.txt 中 lint-report 仍为 Exit code 1。
2. project_state/codex_execution_report.md 顶部仍声称 SUCCESS/ACCEPT，与失败测试记录冲突。
3. codex_execution_report.md 正文仍残留旧 decision_20260604_local_reverse_training_status_overlay_v1。
```

当前 `project_state/decision_packet.md` 是本轮唯一执行权威。`task_packet.task` 中旧 samplereverse 派生任务只是背景，不覆盖本轮。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 原始样本。
2. 不复制样本到仓库。
3. 不运行 solver。
4. 不生成 candidate 或 flag。
5. 不运行 IDA/Ghidra。
6. 不运行动态调试、runtime probe、Frida、OllyDbg、x64dbg。
7. 不读取完整 solve_reports。
8. 不修改 .codex-skills。
9. 不扩大到 reverse_solving 或 tool_integration 主线。
10. 不重写 local_reverse_training_status.py 的业务逻辑，除非 lint/report 对齐确实需要极小修正。
11. 不伪造 pytest_result；失败命令必须真实修复后再记录 PASSED。
```

允许：

```text
1. 修改 project_state/codex_execution_report.md。
2. 修改 project_state/pytest_result.txt。
3. 如 lint-report 需要，可对报告文本做最小范围修正。
4. 只在必要时重新运行现有 status overlay CLI，确认产物未回退。
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
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
```

必要时检查：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
tests/test_project_state.py
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
1. lint-report 是否重新运行并通过，Exit code 是否为 0。
2. git diff --check 是否重新运行并通过。
3. git status --short 是否重新运行并记录。
4. codex_execution_report.md 是否不再残留旧 decision_20260604_local_reverse_training_status_overlay_v1。
5. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_fix_training_status_overlay_report_lint_v1。
6. pytest_result.txt 的 decision_id/report_id/round_id 是否与本轮对齐。
7. codex_execution_report.md 的 status/acceptance_recommendation 是否与 pytest_result.txt 的真实结果一致。
8. status_overlay.json 是否仍是 29 个真实样本，不是 todo1/todo.exe fixture。
9. local_reverse_evaluation_queue.json 是否仍不显示错误的 0 bytes。
10. 是否没有上传原始样本。
11. 是否没有运行 solver、IDA/Ghidra 或动态分析。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如确有必要，允许只为重新生成一致产物而更新：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
```

不应修改：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
```

除非发现 lint/report 对齐必须依赖极小修正，并在报告中说明理由。

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_inventory.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

可以额外运行：

```text
python -m pytest -q tests/test_local_samples.py
```

所有 required commands 必须记录真实 Exit code 0。若任一命令失败，codex_execution_report.md 不得写 SUCCESS/ACCEPT。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. lint-report 仍失败且无法通过只改 report/pytest_result 小范围修复。
2. 修复 report/lint 需要改动业务逻辑或重新设计 status overlay。
3. status_overlay.json 回退为 fixture 或样本数不再是 29。
4. evaluation queue 再次出现错误的 0 bytes。
5. 需要运行 solver、IDA/Ghidra 或动态分析才能完成本轮。
6. 输出会泄露 E:\reverse 或其他真实本地绝对路径。
```

完成条件：

```text
1. lint-report 通过，Exit code 0。
2. pytest_result.txt 所有 required commands 均 Exit code 0。
3. codex_execution_report.md 与 pytest_result.txt 对齐本 decision_id。
4. codex_execution_report.md 不残留旧 decision id。
5. status_overlay.json 仍对应真实 29 个样本。
6. evaluation queue 仍保留真实 size_bytes。
7. 未上传任何原始样本。
```

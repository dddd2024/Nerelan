```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_fix_local_reverse_inventory_remaining_audit_v1",
  "round_id": "round_20260604_fix_local_reverse_inventory_remaining_audit_v1",
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

本轮目标是修复上一轮 `fix_local_reverse_inventory_audit_findings_v1` 后仍残留的两个审计阻断点。上一轮已经修复了 inventory 污染和 cases 的 `LOCAL_REVERSE_ROOT` 占位策略，但测试记录和 project_state 路径策略仍不满足审计要求。

本轮只做最小返工，不进入样本求解，不运行动态分析，不上传原始样本。

必须完成：

```text
1. 从 project_state/local_reverse_inventory.json 中移除真实本地路径 E:\reverse。
2. 如果 reverse_agent/local_reverse_inventory.py 会重新生成该字段，同步修复生成逻辑。
3. 补齐 project_state/pytest_result.txt 中缺失的 lint-report、git diff --check、git status --short 记录。
4. 同步更新 project_state/codex_execution_report.md，使 tests_ran 与 pytest_result.txt 一致。
```

---

## 2. Current Evidence

上一轮审计结论仍为 `REWORK_REQUIRED`。

已修复：

```text
1. inventory 已过滤 .idea、.vscode、.git、__pycache__ 等工程目录。
2. inventory 不再以 .idea 配置文件作为前置条目。
3. cases/*.json 的 input_value 已改为 ${LOCAL_REVERSE_ROOT}/<relative_path>。
4. tests/test_local_reverse_inventory.py 已扩展到 17 passed。
```

仍未修复：

```text
1. project_state/pytest_result.txt 没有记录：
   - python -m reverse_agent.project_state lint-report --state-dir project_state
   - git diff --check
   - git status --short
2. project_state/codex_execution_report.md 的 tests_ran 没有列出完整命令。
3. project_state/local_reverse_inventory.json 仍包含 source_root_label = E:\reverse。
```

当前任务仍由本 `project_state/decision_packet.md` 控制。`task_packet.task` 中的旧 samplereverse 派生任务只是背景，不覆盖本轮。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 中的原始样本文件。
2. 不复制 E:\reverse 到仓库。
3. 不提交 local_reverse_samples 下的本地内容。
4. 不提交 solve_reports 全量目录。
5. 不运行动态分析、调试或 runtime probe。
6. 不生成 candidate、flag 或 solver result。
7. 不修改 .codex-skills。
8. 不扩大到 reverse_solving 或 tool_integration 主线。
9. 不引入数据库、服务端平台或重型工作流系统。
10. 不重做大范围 inventory 设计。
```

允许：

```text
1. 修改 source_root_label/root hint 生成逻辑。
2. 更新 project_state/local_reverse_inventory.json。
3. 更新 project_state/codex_execution_report.md。
4. 更新 project_state/pytest_result.txt。
5. 必要时增加 focused unit test，证明真实本地路径不会进入可提交 project_state inventory。
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
reverse_agent/local_reverse_inventory.py
tests/test_local_reverse_inventory.py
project_state/local_reverse_inventory.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/
```

不要默认读取完整 solve_reports、完整 PROJECT_PROGRESS_LOG.txt 或完整 rounds 历史。

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. project_state/local_reverse_inventory.json 是否不再提交 E:\reverse 或其他真实本地绝对路径。
2. local_reverse_inventory.py 重新生成 inventory 时是否不会把真实本地路径写入可提交字段。
3. GitHub-safe inventory 是否仍只包含 LOCAL_REVERSE_ROOT hint、relative_path 和 metadata。
4. cases metadata 是否仍使用 ${LOCAL_REVERSE_ROOT}/<relative_path>。
5. 是否没有提交原始样本、本地样本目录或完整运行产物目录。
6. 是否没有运行动态分析、调试或 runtime probe。
7. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_fix_local_reverse_inventory_remaining_audit_v1。
8. pytest_result.txt 是否记录真实测试命令，并包含 lint-report、git diff --check、git status --short。
9. codex_execution_report.md 的 tests_ran 是否与 pytest_result.txt 对齐。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_reverse_inventory.py
tests/test_local_reverse_inventory.py
project_state/local_reverse_inventory.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时允许重新生成：

```text
training_materials/local_reverse/inventory.json
training_materials/local_reverse/cases/*.json
```

推荐修复方式：

```text
1. 将 project_state/local_reverse_inventory.json 中的 source_root_label 改为 LOCAL_REVERSE_ROOT 或 user_configured_local_reverse_root。
2. 修改 scan_samples() 生成 local inventory 的逻辑，不再写入 str(samples_root.resolve())。
3. 如果仍需要记录 root 来源，只记录 samples_root_hint = LOCAL_REVERSE_ROOT。
4. 增加或更新测试，确认 inventory JSON 中不含 E:\reverse。
5. 运行完整测试与检查命令，并把结果写入 pytest_result.txt。
6. 更新 codex_execution_report.md，使报告不再声称未记录的命令已经执行。
```

---

## 7. Tests

必须运行并记录：

```text
python -m py_compile reverse_agent/local_reverse_inventory.py
python -m pytest -q tests/test_local_reverse_inventory.py
python -m pytest -q tests/test_local_samples.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

测试最低覆盖：

```text
1. project_state inventory 不含 E:\reverse 或其他真实本地绝对路径。
2. GitHub-safe inventory 不含真实本地绝对路径。
3. cases input_value 仍使用 LOCAL_REVERSE_ROOT 占位符。
4. cases metadata 可被 harness loader 读取。
5. 缺失 samples root 时仍给出清晰错误。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 需要保留真实本地绝对路径才能让现有流程工作。
2. 修复 root hint 需要修改 harness.py 才能兼容。
3. lint-report、git diff --check 或 git status --short 失败且无法小范围修复。
4. 需要上传原始样本才能继续。
```

完成条件：

```text
1. project_state/local_reverse_inventory.json 不再包含 E:\reverse。
2. local_reverse_inventory.py 重新生成时也不会写入真实本地路径。
3. pytest_result.txt 记录所有要求命令。
4. codex_execution_report.md 与 pytest_result.txt 对齐本 decision_id。
5. 未提交任何原始样本。
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_fix_training_status_overlay_audit_v1",
  "round_id": "round_20260604_fix_training_status_overlay_audit_v1",
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

本轮目标是修复上一轮 `local_reverse_training_status_overlay_v1` 的审计阻断点。上一轮已经新增训练集状态 overlay，但审计发现：

```text
1. project_state/pytest_result.txt 中 lint-report 失败，不能接受 SUCCESS。
2. training_materials/local_reverse/status_overlay.json 被测试 fixture 覆盖成 todo1/todo.exe。
3. local_reverse_evaluation_queue.json 中大量 reason 显示 PE sample (0 bytes)，说明 size_bytes 没有从 inventory 传递到 queue。
4. codex_execution_report.md 声称 SUCCESS/ACCEPT，但测试记录中存在失败命令。
```

本轮只做最小返工：修复测试隔离、重新生成真实 status_overlay、保留 size_bytes、补齐通过的测试记录和报告。

本轮不进入 reverse_solving，不运行 solver，不运行 IDA/Ghidra，不运行动态分析，不上传原始样本。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 控制本轮执行。`task_packet.task` 中旧 samplereverse 派生任务仍只是背景，不覆盖本轮。

上一轮产物中可接受的部分：

```text
1. project_state/local_reverse_training_status.json 已生成 29 个样本状态。
2. Cpp1.exe 被标记为 solved，candidate = hookapi。
3. sha_256.exe 被标记为 blocked，blocked_reason = NO_BOUNDED_HASH_PREIMAGE_DOMAIN。
4. CPP2.exe 被标记为 blocked，没有误标为 solved。
5. project_state/local_reverse_evaluation_queue.json 已生成 evaluation queue。
```

仍需返工的问题：

```text
1. pytest_result.txt 中 lint-report 为 Exit code 1。
2. training_materials/local_reverse/status_overlay.json 当前只有 1 个 fixture 样本 todo1/todo.exe，而不是真实 29 个 inventory 样本。
3. tests/test_local_reverse_training_status.py 的 test_main_cli_build 没有把 --github-status-out 指向 tmp_path，导致测试污染真实仓库产物。
4. _build_sample_entry() 未保留 size_bytes，导致 _queue_reason() 默认显示 0 bytes。
5. codex_execution_report.md 顶部 status/acceptance_recommendation 与失败测试记录冲突。
```

当前 negative_results 中仍禁止提交 full solve_reports、回到 old sample_solver blind search、重复无新增证据的旧 probe/audit 方向。本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不上传 E:\reverse 原始样本。
2. 不复制样本到仓库。
3. 不运行 solver。
4. 不生成 candidate。
5. 不运行 IDA/Ghidra。
6. 不运行动态调试、runtime probe、Frida、OllyDbg、x64dbg。
7. 不读取完整 solve_reports。
8. 不修改 .codex-skills。
9. 不扩大到 reverse_solving 或 tool_integration 主线。
10. 不重写 inventory/corpus/training status 三套结构。
11. 不伪造 pytest_result；失败命令必须真实修复后再记录 PASSED。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_training_status.py 中 size_bytes 传递和 queue reason 逻辑。
2. 修改 tests/test_local_reverse_training_status.py，保证所有测试输出写入 tmp_path。
3. 重新生成 training_materials/local_reverse/status_overlay.json。
4. 重新生成 project_state/local_reverse_training_status.json 和 project_state/local_reverse_evaluation_queue.json。
5. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
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
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_inventory.json
training_materials/local_reverse/inventory.json
project_state/local_reverse_validated_candidate_handoff.json
project_state/local_reverse_constraint_recovery_result.json
project_state/local_reverse_ida_solver_result.json
```

必要时检查：

```text
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
tests/test_local_reverse_inventory.py
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
1. lint-report 是否重新运行并通过。
2. git diff --check 是否重新运行并通过。
3. git status --short 是否重新运行并记录。
4. tests/test_local_reverse_training_status.py 是否不再写 training_materials/local_reverse/status_overlay.json 真实路径。
5. status_overlay.json 是否对应真实 inventory，而不是 todo1/todo.exe fixture。
6. status_overlay.json 是否包含 29 个样本，且 status_summary 与 project_state/local_reverse_training_status.json 一致。
7. local_reverse_evaluation_queue.json 的 reason 是否不再错误显示 0 bytes，除非原始 inventory 的 size_bytes 真为 0。
8. _build_sample_entry() 是否保留 size_bytes 或等价字段。
9. Cpp1.exe 是否仍为 solved/validated。
10. sha_256.exe 是否仍为 blocked: NO_BOUNDED_HASH_PREIMAGE_DOMAIN。
11. CPP2.exe 是否仍为 blocked 或 needs_solver，不能声称 solved。
12. 是否没有上传原始样本。
13. 是否没有运行 solver、IDA/Ghidra 或动态分析。
14. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_fix_training_status_overlay_audit_v1。
15. codex_execution_report.md 的 status/acceptance_recommendation 是否与 pytest_result.txt 真实结果一致。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

推荐修复方式：

```text
1. 在 _build_sample_entry() 中加入 size_bytes: entry.get("size_bytes", 0)。
2. 确认 _queue_reason() 使用 sample["size_bytes"]，不再全部回落到 0。
3. 修改 test_main_cli_build：显式传入 --github-status-out 到 tmp_path 下的文件。
4. 检查所有测试中调用 main()/build_training_status() 时，输出路径都在 tmp_path。
5. 重新运行 CLI，基于真实 project_state/local_reverse_inventory.json 生成 status_overlay.json。
6. 确认 training_materials/local_reverse/status_overlay.json 不含 todo1/todo.exe。
7. 修复导致 lint-report 失败的 report/decision/report_id 对齐问题。
8. 重新记录 pytest_result.txt，所有 required commands 必须 Exit code 0。
```

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

测试最低覆盖：

```text
1. test_main_cli_build 不污染真实 training_materials/local_reverse/status_overlay.json。
2. build_training_status 输出的 github_status 与真实 inventory 数量一致。
3. queue reason 使用真实 size_bytes。
4. Cpp1 solved、sha_256 blocked、CPP2 blocked 的状态不回退。
5. status_overlay 不含真实本地绝对路径。
6. solved/blocked 样本不进入 evaluation queue。
7. lint-report 通过。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. lint-report 仍失败且无法小范围修复。
2. status_overlay 不能从真实 inventory 重新生成。
3. 修复测试隔离需要大范围改 CLI 设计。
4. 需要运行 solver、IDA/Ghidra 或动态分析才能完成本轮。
5. 输出会泄露 E:\reverse 或其他真实本地绝对路径。
```

完成条件：

```text
1. lint-report 通过。
2. status_overlay.json 不再是 todo1/todo.exe fixture。
3. status_overlay.json 与真实 29 个样本状态一致。
4. evaluation queue 不再错误显示 0 bytes。
5. pytest_result.txt 记录所有 required commands 且全部 Exit code 0。
6. codex_execution_report.md 与 pytest_result.txt 对齐本 decision_id。
7. 未上传任何原始样本。
```

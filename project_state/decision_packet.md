```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_training_status_lint_report_rework_v1",
  "round_id": "round_20260605_affine_training_status_lint_report_rework_v1",
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

上一轮 `decision_20260605_affine_training_status_overlay_rework_v1` 审计结论为 `REWORK_REQUIRED`。核心代码返工已经基本正确：

```text
1. static handoff overlay 已收紧为只接受 BLOCKED 静态 handoff。
2. READY + candidate static handoff 已不会把样本标记 solved。
3. affine_8cfebe03 已保持 blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""。
4. affine_8cfebe03 已不在 local_reverse_evaluation_queue.json。
```

但本轮仍有一个验收缺口：

```text
required command 缺失：
python -m reverse_agent.project_state lint-report --state-dir project_state

该命令没有出现在 codex_report_summary.tests_ran，也没有出现在 pytest_result.txt。
```

本轮目标：**只修复 lint-report 测试记录缺口，并同步 report / pytest_result。**

除非 `lint-report` 暴露必须修复的问题，否则本轮不得修改核心训练状态逻辑。

---

## 2. Current Evidence

当前 `task_packet.json` 仍含旧 samplereverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已完成且应保持：

```text
reverse_agent/local_reverse_training_status.py:
  _build_static_handoff_overlay() 只接受：
    static_only is true
    executed_sample is false
    runtime_validated is false
    status == BLOCKED
    candidate is None
    blocked_reason 非空

project_state/local_reverse_training_status.json:
  affine_8cfebe03.training_status == blocked
  affine_8cfebe03.blocked_reason == MISSING_EXPECTED_CIPHERTEXT
  affine_8cfebe03.known_candidate == ""
  affine_8cfebe03.classification includes affine_cipher / static only / missing_expected_ciphertext
  affine_8cfebe03.evidence_sources includes source:local_reverse_affine_inverse_handoff.json, static_handoff, static_cipher_analysis

project_state/local_reverse_evaluation_queue.json:
  affine_8cfebe03 not in items

现有 solved/blocked 状态应保持：
  cpp1_bcbd9979 remains solved
  cpp2_4c69f173 remains blocked
  sha_256_18019fca remains blocked
```

当前缺失：

```text
codex_execution_report.md:
  codex_report_summary.tests_ran 缺少 lint-report

pytest_result.txt:
  缺少 python -m reverse_agent.project_state lint-report --state-dir project_state 的 Command / Exit Code / Output / Result 记录
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行任何本地样本。
3. 不运行 runtime probe、debugger、Frida、OllyDbg、x64dbg、emulator。
4. 不运行 old sample_solver blind search。
5. 不生成 flag、candidate 或 known_candidate。
6. 不把 static handoff 的 READY + candidate 标记为 solved。
7. 不把静态 handoff 说成 runtime validation。
8. 不发明 expected_ciphertext。
9. 不把 MISSING_EXPECTED_CIPHERTEXT 改写成 solved。
10. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
11. 不提交 full solve_reports、IDA .i64、log 或原始样本。
12. 不修改 .codex-skills。
13. 不新建第二套训练状态系统。
14. 不重写 static handoff overlay 逻辑。
15. 不扩大到批量跑训练集。
```

允许：

```text
1. 运行 required tests，包括 lint-report。
2. 如果 lint-report 暴露真实错误，允许最小修复相关 report/metadata 字段。
3. 更新 codex_execution_report.md。
4. 更新 pytest_result.txt。
5. 如重新运行 training_status CLI 导致 generated_at 变化，允许同步更新 local_reverse_training_status.json 和 local_reverse_evaluation_queue.json，但不得改变语义。
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
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
```

必要时检查：

```text
tests/test_project_state.py
project_state/local_reverse_affine_inverse_handoff.json
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
3. 是否确认本轮主线为 training_dataset，且没有扩大到 reverse_solving / tool_integration。
4. 是否确认本轮只是 lint-report 记录返工。
5. 是否运行 python -m reverse_agent.project_state lint-report --state-dir project_state。
6. 是否将 lint-report 写入 codex_report_summary.tests_ran。
7. 是否将 lint-report 写入 pytest_result.txt，包含 Command / Exit Code / Output / Result。
8. 是否确认 lint-report Exit Code 0。
9. 是否确认 affine_8cfebe03 仍为 training_status=blocked。
10. 是否确认 affine_8cfebe03 blocked_reason=MISSING_EXPECTED_CIPHERTEXT。
11. 是否确认 affine_8cfebe03 known_candidate=""。
12. 是否确认 affine_8cfebe03 不在 local_reverse_evaluation_queue.json。
13. 是否确认 cpp1_bcbd9979 remains solved。
14. 是否确认 cpp2_4c69f173 remains blocked。
15. 是否确认 sha_256_18019fca remains blocked。
16. 是否没有运行 affine.exe 或任何本地样本。
17. 是否没有运行 runtime probe、debugger、emulator。
18. 是否没有提交 solve_reports、IDA .i64、log、原始样本。
19. 是否没有修改 .codex-skills。
20. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_training_status_lint_report_rework_v1。
21. codex_report_summary.tests_ran 是否完整列出 required commands，包括 lint-report。
22. pytest_result.txt 是否记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

首选路径：不改核心代码，只补测试执行与记录。

必须保持：

```text
1. static handoff overlay 只接受 BLOCKED 静态 handoff。
2. READY + candidate static handoff 不能把样本标记 solved。
3. affine_8cfebe03 保持 blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""。
4. affine_8cfebe03 不在 local_reverse_evaluation_queue.json。
```

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅当重新运行命令造成 generated_at 或输出文件变化时，允许同步修改：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
```

仅当 lint-report 暴露必须修复的问题时，才允许最小修改：

```text
reverse_agent/local_reverse_training_status.py
tests/test_local_reverse_training_status.py
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_training_status.py
python -m pytest -q tests/test_local_reverse_training_status.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_training_status --artifact-index project_state/artifact_index.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

允许额外运行但不得替代 required commands：

```bash
python -m pytest -q tests/test_local_reverse_affine_inverse_handoff.py
```

测试期望：

```text
1. 所有 required commands Exit Code 0。
2. lint-report 出现在 codex_report_summary.tests_ran。
3. lint-report 出现在 pytest_result.txt。
4. affine_8cfebe03 仍为 blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""。
5. affine_8cfebe03 不在 local_reverse_evaluation_queue.json。
6. git status --short 不出现 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. lint-report 失败且无法在本轮范围内小步修复。
2. 需要运行 affine.exe 或任何本地样本才能完成。
3. 需要 runtime probe/debugger/emulator 才能完成。
4. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG 才能完成。
5. 需要提交 solve_reports、IDA .i64、log 或原始样本才能完成。
6. 需要修改 .codex-skills 才能完成。
7. 重新运行导致 affine_8cfebe03 从 blocked 回退或生成 candidate。
8. 重新运行导致 solved/blocked 样本状态回退。
```

完成条件：

```text
1. lint-report 运行并 Exit Code 0。
2. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision。
3. codex_report_summary.tests_ran 完整列出 required commands，包括 lint-report。
4. pytest_result.txt 记录 lint-report 的 Command / Exit Code / Output / Result。
5. affine_8cfebe03 保持 blocked / MISSING_EXPECTED_CIPHERTEXT / known_candidate=""。
6. affine_8cfebe03 不再出现在 local_reverse_evaluation_queue.json。
7. cpp1_bcbd9979 remains solved。
8. cpp2_4c69f173 remains blocked。
9. sha_256_18019fca remains blocked。
10. 未运行样本、runtime probe、debugger、emulator、old sample_solver blind search。
11. 未提交 solve_reports、IDA .i64、log、原始样本、.codex-skills。
```

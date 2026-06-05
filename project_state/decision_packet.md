```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_cleanup_test_record_rework_v1",
  "round_id": "round_20260605_cpp1_cleanup_test_record_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **engineering_branch**。

目标：只修复上一轮 `round_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1` 的测试记录和报告不完整问题。

上一轮清理方向基本正确，但存在三个验收阻断点：

```text
1. required command 缺失：
   python -m py_compile reverse_agent/local_reverse_cpp1_inverse_handoff.py

2. required command 缺失：
   git diff --name-status

3. codex_execution_report.md 的 files_changed 不完整：
   只列出 report/pytest/overlay，没有列出实际删除的 IDA 副产物和 tests/__init__.py。
```

本轮不得改 inverse handoff 核心逻辑，不得重新运行 IDA，不得动态执行样本。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮 report：

```text
report_id=report_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1
based_on_decision_id=decision_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPT
```

但审计发现：

```text
1. tests_ran 未包含 py_compile。
2. tests_ran 未包含 git diff --name-status。
3. pytest_result.txt 未记录 py_compile。
4. pytest_result.txt 未记录 git diff --name-status。
5. files_changed 与 git status / actual cleanup diff 不一致。
```

当前 inverse handoff artifact 保持：

```text
runtime_validated=false
candidate=null
known_candidate=""
status=BLOCKED
blocked_reason=STATIC_CANDIDATE_NONPRINTABLE
```

实际 cleanup diff 应包含删除项与记录文件修改。Codex 必须以本轮本地 `git diff --name-status` 输出为准，不得只按自报 files_changed 编写 report。

---

## 3. Do Not Do

严禁：

```text
1. 不修改 reverse_agent/local_reverse_cpp1_inverse_handoff.py，除非 py_compile 暴露确定语法问题。
2. 不重新运行 IDA。
3. 不重新生成 IDA artifact。
4. 不动态执行样本。
5. 不做 runtime validation。
6. 不运行 solver / brute force。
7. 不写 known_candidate。
8. 不把 cpp1_2f6fcb63 标记 solved。
9. 不修改 .codex-skills。
10. 不新增或恢复 IDA .i64、IDA log、extract/triage 目录。
11. 不改 artifact_index，除非发现登记损坏。
12. 不把本轮 test/report 修复包装成新的逆向进展。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 补跑 py_compile。
3. 补跑 git diff --name-status。
4. 同步 project_state/codex_execution_report.md。
5. 同步 project_state/pytest_result.txt。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
reverse_agent/local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_inverse_handoff.py
```

必须检查：

```bash
git status --short
git diff --name-status
git diff --check
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
3. 是否确认本轮主线为 engineering_branch。
4. 是否确认本轮只是 test/report record rework。
5. 是否补跑 py_compile reverse_agent/local_reverse_cpp1_inverse_handoff.py。
6. 是否补跑 git diff --name-status。
7. 是否 pytest_result.txt 记录 py_compile 的 Command、Exit Code、Output、Result。
8. 是否 pytest_result.txt 记录 git diff --name-status 的 Command、Exit Code、Output、Result。
9. 是否 codex_execution_report.md 的 tests_ran 完整列出 required commands。
10. 是否 codex_execution_report.md 的 files_changed 与 git diff --name-status 完全一致。
11. 是否没有恢复 IDA .i64、IDA log、extract/triage 目录。
12. 是否 inverse handoff artifact 仍为 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
13. 是否 inverse handoff artifact 仍为 runtime_validated=false、candidate=null、known_candidate=""。
14. 是否没有重新运行 IDA。
15. 是否没有动态执行样本。
16. 是否没有 runtime validation。
17. 是否没有运行 solver / brute force。
18. 是否没有修改 .codex-skills。
```

---

## 6. Implementation Scope

只允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

除非发现确定错误，否则不得修改其他文件。

`codex_execution_report.md` 的 `files_changed` 必须包含实际 diff 中所有文件，包括删除项。例如若当前 diff 仍包含：

```text
D project_state/extract_cpp1_2f6fcb63/ida_extract.i64
D project_state/extract_cpp1_2f6fcb63/ida_extract.log
D project_state/extract_cpp1_2f6fcb63/named_data_extract.json
D project_state/triage_cpp1_2f6fcb63/ida_evidence.json
D project_state/triage_cpp1_2f6fcb63/ida_triage.i64
D project_state/triage_cpp1_2f6fcb63/ida_triage.log
D tests/__init__.py
M training_materials/local_reverse/status_overlay.json
M project_state/codex_execution_report.md
M project_state/pytest_result.txt
```

则 report 必须完整列出这些路径。

如果 `git diff --name-status` 和上述示例不同，以实际命令输出为准。

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

可选但允许保留：

```bash
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
```

Expected results：

```text
1. All required commands Exit Code 0。
2. py_compile 已记录。
3. git diff --name-status 已记录。
4. report tests_ran 完整。
5. pytest_result.txt 完整。
6. files_changed 与实际 diff 完全一致。
7. 不产生新的代码逻辑变更。
8. inverse handoff artifact 仍为 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
9. inverse handoff artifact 仍为 runtime_validated=false、candidate=null、known_candidate=""。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. py_compile 失败。
2. git diff --name-status 显示恢复了 IDA .i64、IDA log、extract/triage 目录。
3. inverse handoff artifact 丢失。
4. inverse handoff artifact 出现 runtime_validated=true。
5. inverse handoff artifact 出现 candidate 非 null 或 known_candidate 非空。
6. report 的 files_changed 无法与 git diff --name-status 对齐。
7. 需要重新运行 IDA 才能完成。
8. 需要动态执行样本或 runtime validation 才能完成。
```

完成条件：

```text
1. project_state/codex_execution_report.md 与 project_state/pytest_result.txt 对齐当前 decision_id/round_id。
2. required tests 全部记录。
3. files_changed 与实际 git diff --name-status 完全一致。
4. 未修改 reverse_agent/local_reverse_cpp1_inverse_handoff.py。
5. 未恢复 IDA 副产物。
6. 未动态执行样本，未 runtime validation，未写 known_candidate，未标记 solved。
```

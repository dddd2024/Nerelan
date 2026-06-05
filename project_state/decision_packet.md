```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_transform_recheck_record_fix_v1",
  "round_id": "round_20260605_cpp1_transform_recheck_record_fix_v1",
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

目标：修复上一轮 `round_20260605_cpp1_transform_semantics_recheck_v1` 的记录与 evidence metadata 问题，不推进新求解。

上一轮 transform recheck 主体方向可以保留，但存在验收阻断点，必须轻量返工：

```text
1. decision_packet.md 中 based_on_state_digest 错误，导致 lint-decision failed。
2. codex_execution_report.md 不能在 lint-decision failed 时写 SUCCESS / ACCEPT。
3. pytest_result.txt 不能在 1 failed 时写 status=PASSED。
4. transform_recheck artifact 和脚本中的 forward bit_mapping 错误：y7=y3 应为 y7=x3。
```

本轮只修复上述问题，不动态执行样本，不运行 IDA，不做 runtime validation，不把样本标记 solved。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮 report：

```text
report_id=report_20260605_cpp1_transform_semantics_recheck_v1
based_on_decision_id=decision_20260605_cpp1_transform_semantics_recheck_v1
status=SUCCESS
acceptance_recommendation=ACCEPT
```

但审计发现：

```text
1. lint-decision Exit Code 1。
2. pytest_result.txt summary 写 status=PASSED，但 Total Tests=10 / Passed=9 / Failed=1。
3. codex_execution_report.md 顶部写 SUCCESS / ACCEPT，与 required command failure 矛盾。
4. reverse_agent/local_reverse_cpp1_transform_recheck.py 中 forward_transform.bit_mapping 写成 y7=y3。
5. project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json 中 forward_transform.bit_mapping 同样写成 y7=y3。
```

当前正确 digest 应为：

```text
4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

当前错误 digest 为重复拼接版本：

```text
4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c3e80ca4413678c
```

上一轮可保留的核心结论：

```text
1. transform_recheck artifact 已生成并登记 artifact_index。
2. artifact status=BLOCKED。
3. blocked_reason=NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM。
4. candidate=null。
5. known_candidate=""。
6. runtime_validated=false。
7. 没有看到 IDA .i64、IDA log、原始样本或 full solve_reports 被提交。
```

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行样本。
2. 不运行 IDA。
3. 不重新生成 IDA artifact。
4. 不做 runtime validation。
5. 不运行 solver / brute force。
6. 不写 candidate。
7. 不写 known_candidate。
8. 不标记 solved。
9. 不修改 local_reverse_training_status.json 为 solved。
10. 不提交 IDA .i64、IDA log、原始样本、full solve_reports。
11. 不修改 .codex-skills。
12. 不扩大到其他样本。
13. 不把本轮记录修复包装成新的逆向求解进展。
```

允许：

```text
1. 修复 decision_packet.md 的 based_on_state_digest。
2. 修复 transform_recheck 脚本中的 bit_mapping metadata。
3. 重新运行 transform_recheck CLI，更新 transform_recheck artifact。
4. 更新 artifact_index 中 transform_recheck artifact 的 sha256、size_bytes、modified_at。
5. 更新 codex_execution_report.md。
6. 更新 pytest_result.txt。
7. 在测试中增加 bit_mapping metadata 断言。
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
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
reverse_agent/local_reverse_cpp1_transform_recheck.py
tests/test_local_reverse_cpp1_transform_recheck.py
```

可检查但不得默认重型读取：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
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
4. 是否确认本轮只做记录与 metadata 修复。
5. 是否修复 based_on_state_digest。
6. 是否补跑 lint-decision 且 Exit Code 0。
7. 是否修复 pytest_result summary，使其与详细结果一致。
8. 是否修复 codex_execution_report status / acceptance。
9. 是否修复 y7=y3 为 y7=x3。
10. 是否重新生成 transform_recheck artifact。
11. 是否更新 artifact_index 中 transform_recheck artifact 的 sha256、size_bytes、modified_at。
12. 是否 artifact 仍为 candidate=null。
13. 是否 artifact 仍为 known_candidate=""。
14. 是否 artifact 仍为 runtime_validated=false。
15. 是否 artifact 仍为 BLOCKED / NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM。
16. 是否没有运行 IDA。
17. 是否没有动态执行样本。
18. 是否没有 runtime validation。
19. 是否没有恢复 IDA .i64、IDA log、原始样本、full solve_reports。
20. 是否 tests_ran 完整列出 required commands。
21. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/decision_packet.md
reverse_agent/local_reverse_cpp1_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许修改测试：

```text
tests/test_local_reverse_cpp1_transform_recheck.py
```

但仅限补充 bit_mapping metadata 断言，避免再次出现 y7=y3 这类 artifact metadata 错误。

不得修改：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_target_byte_extract.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
.codex-skills/*
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_inverse_handoff.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_transform_recheck --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --inverse-handoff project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --out project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

可选但允许：

```bash
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
```

Expected results：

```text
1. All required commands Exit Code 0。
2. lint-decision Exit Code 0。
3. lint-report Exit Code 0。
4. pytest_result summary 与详细记录一致。
5. report status/acceptance 与测试结果一致。
6. forward_transform.bit_mapping 包含 y7=x3，不包含 y7=y3。
7. transform_recheck artifact 仍为 BLOCKED / NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM。
8. candidate=null，known_candidate=""。
9. runtime_validated=false。
10. git diff --name-status 只包含本轮允许范围内的文件。
11. 不产生 IDA .i64、IDA log、solve_reports、原始样本提交。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. lint-decision 仍失败。
2. lint-report 失败。
3. transform_recheck artifact 丢失。
4. artifact 出现 candidate 非 null。
5. artifact 出现 known_candidate 非空。
6. artifact 出现 runtime_validated=true。
7. bit_mapping 仍包含 y7=y3。
8. 需要运行 IDA 才能完成。
9. 需要动态执行样本才能完成。
10. git status 出现 IDA .i64、IDA log、原始样本、full solve_reports 或无关文件。
```

完成条件：

```text
1. 所有 required commands Exit Code 0。
2. pytest_result summary 与详细记录一致。
3. codex_execution_report 不再把失败测试写成 SUCCESS。
4. bit_mapping 修复为 y7=x3。
5. artifact_index hash/size 与重新生成 artifact 一致。
6. 样本仍为 BLOCKED，不写 candidate / known_candidate，不标记 solved。
```
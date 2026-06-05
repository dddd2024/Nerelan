```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1",
  "round_id": "round_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1",
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

目标：清理上一轮 `decision_20260605_cpp1_inverse_transform_handoff_v1` 的提交范围违规问题。

上一轮审计结论：`REWORK_REQUIRED`。

核心问题：Codex 报告自称只修改/新增 6 个文件，但实际 GitHub commit 对比显示还提交了 IDA `.i64`、IDA log、临时 extraction/triage 目录、training overlay 和无关 `tests/__init__.py`。这些文件不在上一轮 decision 允许范围内，且部分命中 Do Not Do。

本轮只做范围清理和报告同步，不推进样本求解，不重新运行 IDA，不动态执行样本。

必须保留上一轮符合范围的成果：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_inverse_handoff.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须删除或回退上一轮误提交的越界文件/修改：

```text
project_state/extract_cpp1_2f6fcb63/ida_extract.i64
project_state/extract_cpp1_2f6fcb63/ida_extract.log
project_state/extract_cpp1_2f6fcb63/named_data_extract.json
project_state/triage_cpp1_2f6fcb63/ida_evidence.json
project_state/triage_cpp1_2f6fcb63/ida_triage.i64
project_state/triage_cpp1_2f6fcb63/ida_triage.log
tests/__init__.py
training_materials/local_reverse/status_overlay.json
```

完成后，`project_state/codex_execution_report.md` 的 `files_changed` 必须与实际 `git diff --name-status` 完全一致。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。当前轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮 decision：

```text
decision_20260605_cpp1_inverse_transform_handoff_v1
round_20260605_cpp1_inverse_transform_handoff_v1
mainline=reverse_solving
```

上一轮 Codex report 自报：

```text
status=SUCCESS
acceptance_recommendation=ACCEPT
files_changed=[
  reverse_agent/local_reverse_cpp1_inverse_handoff.py,
  tests/test_local_reverse_cpp1_inverse_handoff.py,
  project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json,
  project_state/artifact_index.json,
  project_state/codex_execution_report.md,
  project_state/pytest_result.txt
]
```

审计发现实际 GitHub compare `7ce196e75782d8a6d83b4de101842b8677b0a807..266c4fa706a26c4e104941766894c8d9e4933736` 还包含：

```text
project_state/extract_cpp1_2f6fcb63/ida_extract.i64
project_state/extract_cpp1_2f6fcb63/ida_extract.log
project_state/extract_cpp1_2f6fcb63/named_data_extract.json
project_state/triage_cpp1_2f6fcb63/ida_evidence.json
project_state/triage_cpp1_2f6fcb63/ida_triage.i64
project_state/triage_cpp1_2f6fcb63/ida_triage.log
tests/__init__.py
training_materials/local_reverse/status_overlay.json
```

这些越界文件违反上一轮 decision 的 Do Not Do：不提交原始样本、full solve_reports、IDA 数据库副产物或无必要日志；不扩大到无关文件；不写入未授权 training overlay。

可保留部分：

```text
1. reverse_agent/local_reverse_cpp1_inverse_handoff.py 的静态 inverse handoff 逻辑可保留。
2. tests/test_local_reverse_cpp1_inverse_handoff.py 可保留。
3. project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json 可保留。
4. artifact_index 中 local_reverse_cpp1_2f6fcb63_inverse_handoff freshness=current 可保留。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat old dynamic-probe directions without new evidence
```

本轮是工程清理，不得触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不修改 inverse handoff 核心逻辑，除非发现确定 bug。
2. 不重新运行 IDA。
3. 不重新生成 IDA artifact。
4. 不动态执行样本。
5. 不做 runtime validation。
6. 不运行旧盲搜 solver。
7. 不运行 brute force。
8. 不写 known_candidate。
9. 不把 cpp1_2f6fcb63 标记 solved。
10. 不更新 local_reverse_training_status.json 为 solved。
11. 不提交 .i64、IDA log、临时 extraction/triage 目录、full solve_reports 或原始样本。
12. 不修改 .codex-skills。
13. 不扩大到其他样本。
14. 不把 task_packet.task 当执行权威。
15. 不把本轮清理包装成新的逆向求解进展。
```

允许：

```text
1. 读取默认 project_state 事实源。
2. 检查上一轮 commit diff / git diff --name-status。
3. 删除或回退越界 IDA 副产物、IDA log、临时 extraction/triage 目录和 training overlay 修改。
4. 保留 inverse handoff 脚本、测试、artifact 和 artifact_index 登记。
5. 更新 codex_execution_report.md 与 pytest_result.txt，使其反映本轮清理事实。
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
reverse_agent/local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_inverse_handoff.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/artifact_index.json
```

必须检查工作区状态：

```bash
git status --short
git diff --name-status
git diff --check
```

必须删除或回退的越界路径：

```text
project_state/extract_cpp1_2f6fcb63/
project_state/triage_cpp1_2f6fcb63/
tests/__init__.py
training_materials/local_reverse/status_overlay.json
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
4. 是否确认本轮只是范围清理和报告同步。
5. 是否删除/回退所有越界 IDA .i64 文件。
6. 是否删除/回退所有越界 IDA log 文件。
7. 是否删除/回退 project_state/extract_cpp1_2f6fcb63/。
8. 是否删除/回退 project_state/triage_cpp1_2f6fcb63/。
9. 是否删除/回退 tests/__init__.py。
10. 是否删除/回退 training_materials/local_reverse/status_overlay.json 的本轮修改。
11. 是否保留 reverse_agent/local_reverse_cpp1_inverse_handoff.py。
12. 是否保留 tests/test_local_reverse_cpp1_inverse_handoff.py。
13. 是否保留 project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json。
14. 是否确认 artifact_index 中 local_reverse_cpp1_2f6fcb63_inverse_handoff 仍为 freshness=current。
15. 是否确认 inverse handoff artifact 仍为 runtime_validated=false。
16. 是否确认 inverse handoff artifact 仍为 candidate=null / known_candidate=""。
17. 是否确认 inverse handoff artifact 仍为 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
18. 是否没有动态执行样本。
19. 是否没有重新运行 IDA。
20. 是否没有 runtime validation。
21. 是否没有运行 old blind solver / brute force。
22. 是否没有把 cpp1_2f6fcb63 标记 solved。
23. 是否没有修改 .codex-skills。
24. 是否 codex_execution_report.md 的 files_changed 与 git diff --name-status 完全一致。
25. 是否 pytest_result.txt 记录每条 required command、Exit Code 和输出摘要。
26. 是否 git status --short 不再出现 IDA .i64、IDA log、临时 extraction/triage 目录、training overlay、原始样本或 full solve_reports。
```

---

## 6. Implementation Scope

本轮只做清理，不做新功能。

允许保留：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
tests/test_local_reverse_cpp1_inverse_handoff.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/artifact_index.json
```

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须移除或回退：

```text
project_state/extract_cpp1_2f6fcb63/ida_extract.i64
project_state/extract_cpp1_2f6fcb63/ida_extract.log
project_state/extract_cpp1_2f6fcb63/named_data_extract.json
project_state/triage_cpp1_2f6fcb63/ida_evidence.json
project_state/triage_cpp1_2f6fcb63/ida_triage.i64
project_state/triage_cpp1_2f6fcb63/ida_triage.log
tests/__init__.py
training_materials/local_reverse/status_overlay.json
```

如果这些文件已经被提交到远端，必须通过删除提交或后续清理提交移除，不得只在 report 中解释。

`codex_execution_report.md` 顶部必须包含 fenced JSON block：`codex_report_summary`，并且：

```text
based_on_decision_id=decision_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1
round_id=round_20260605_cpp1_inverse_handoff_scope_cleanup_rework_v1
status=SUCCESS 或 BLOCKED
acceptance_recommendation=ACCEPT 或 REWORK
files_changed 必须真实完整
```

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

Expected results：

```text
1. All required commands Exit Code 0。
2. git diff --name-status 只包含本轮允许范围内的文件。
3. git status --short 不包含 IDA .i64、IDA log、临时 extraction/triage 目录、training overlay、原始样本、full solve_reports。
4. codex_execution_report.md 的 files_changed 与实际 diff 一致。
5. pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
6. inverse handoff artifact 仍为 BLOCKED / STATIC_CANDIDATE_NONPRINTABLE。
7. inverse handoff artifact 仍为 runtime_validated=false、candidate=null、known_candidate=""。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 无法删除/回退 IDA .i64 或 IDA log。
2. 无法删除/回退临时 extraction/triage 目录。
3. 清理后 inverse handoff artifact 丢失。
4. 清理后 artifact_index 丢失 local_reverse_cpp1_2f6fcb63_inverse_handoff。
5. 清理需要重新运行 IDA。
6. 清理需要动态执行样本。
7. 清理需要 runtime validation。
8. 清理后 report 与实际 git diff 仍不一致。
9. 清理过程中出现 known_candidate/solved 写入倾向。
```

完成条件：

```text
1. 越界 IDA .i64、IDA log、临时 extraction/triage 目录已删除或回退。
2. training_materials/local_reverse/status_overlay.json 的本轮修改已删除或回退。
3. tests/__init__.py 已删除或回退，除非能证明它早已存在且不是本轮新增；若保留，必须给出证据。
4. inverse handoff 脚本、测试、artifact 保留。
5. artifact_index 中 local_reverse_cpp1_2f6fcb63_inverse_handoff 仍为 freshness=current。
6. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
7. required tests 全部记录。
8. 未动态执行样本，未运行 runtime validation，未修改 .codex-skills，未提交大型副产物或原始样本。
```

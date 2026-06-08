```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_files_changed_rework_v1",
  "round_id": "round_20260608_solver_profile_dispatch_files_changed_rework_v1",
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

目标：返工上一轮 `solver_profile_dispatch_report_consistency_rework` 的 `codex_report_summary.files_changed` 漏列问题，使 `project_state/codex_execution_report.md` 顶部 summary、正文 Required Audit Answers、`project_state/pytest_result.txt` 和实际 diff 范围一致。

当前阻断点不是 solver 逻辑、不是训练集状态、不是逆向样本求解，也不是 artifact 内容错误。上一轮已经把 lint-report 最终状态改为 PASS，并把上一轮漏报的 `project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json` 放入 `generated_artifacts`；但仍不可接受，原因是：

```text
codex_report_summary.files_changed 没有列出 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json，
而正文 Required Audit Answers 声称 “files_changed 是否包含 rework audit artifact？YES”。
```

本轮只允许修复报告 metadata 一致性。不要改 solver 逻辑，不要改测试逻辑，不推进样本求解。

必须完成：

```text
1. 在 project_state/codex_execution_report.md 顶部 codex_report_summary.files_changed 中补入：
   project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json

2. 保留 codex_report_summary.generated_artifacts 中已有的两个 artifact：
   project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
   project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json

3. 确认 codex_report_summary.files_changed 至少包含：
   project_state/codex_execution_report.md
   project_state/pytest_result.txt
   project_state/artifact_index.json
   project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
   project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json

4. 重新运行并记录 project_state lint/status 和 git diff 检查。
5. 如修改 pytest_result.txt，必须绑定当前 files_changed rework decision/report/round。
```

建议产出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt  # 仅当需要更新本轮测试记录时修改
```

默认不要修改：

```text
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
project_state/artifact_index.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

被审计提交：

```text
commit=f3646e2cb0379d72f0167f9f34f0948f72eb4334
message=rework: fix report metadata consistency for guardrails rework round
round=round_20260608_solver_profile_dispatch_report_consistency_rework_v1
decision=decision_20260608_solver_profile_dispatch_report_consistency_rework_v1
```

上一轮已完成的可接受部分：

```text
1. codex_report_summary report_id/round_id/based_on_decision_id 已切到 consistency rework。
2. pytest_result.txt 已绑定 consistency rework，并记录 status=PASSED。
3. pytest_result.txt 记录 pytest=179 passed、lint-decision PASS、lint-report PASS、project_state status PASS、git diff --check PASS。
4. codex_execution_report.md 正文中最终 lint-report 状态已改为 PASS。
5. generated_artifacts 已包含：
   - project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
   - project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
6. diff 未显示 solver production code 修改。
```

上一轮仍不可接受的部分：

```text
1. codex_report_summary.files_changed 只列：
   - project_state/codex_execution_report.md
   - project_state/pytest_result.txt
   - project_state/artifact_index.json
   - project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json

2. codex_report_summary.files_changed 漏列：
   - project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json

3. 正文 Required Audit Answers 写 “files_changed 是否包含 rework audit artifact？YES”，但顶部 summary 不支持这个结论。
```

当前 training summary 应保持不变：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver 和 project_state lint/status 机制。本轮只修 project_state 报告 metadata，不调用成熟逆向工具，不重写反汇编/反编译/调试能力。

`negative_results.json` 主要约束旧 `samplereverse` 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill。本轮 skill_profiles 只能使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要继续推进 cpp2_883e67b9 求解。
2. 不要运行任何 E:\reverse 样本。
3. 不要执行 candidate、negative control 或 runtime validation。
4. 不要 attach debugger / hook / emulator / probe / winpty。
5. 不要调用 IDA/Ghidra 或读取样本二进制。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要修改 local_reverse_training_status.json 中 solved/blocked/inventory 状态。
8. 不要修改 training_materials/local_reverse/status_overlay.json。
9. 不要把 KEEP_DREAM、WeKnowItOk、10013、hookapi 写死进 production solver 或 dispatch。
10. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
11. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
12. 不要重写成熟工具已有的反汇编/反编译能力。
13. 不要读取完整 solve_reports。
14. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不要提交 full solve_reports。
16. 不要把 task_packet.task 当作执行权威。
17. 不要把本轮变成训练状态同步、新样本求解轮、工具动态验证轮或真实 artifact 提取轮。
18. 不要改 solver 逻辑来掩盖报告 metadata 问题。
19. 不要删除 generated_artifacts 中已经正确列出的两个 artifact。
20. 不要让正文 Required Audit Answers 与顶部 codex_report_summary 再次不一致。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮 report、pytest_result、artifact_index、两个 rework audit artifact。
3. 修正 codex_execution_report.md 的 summary files_changed。
4. 如需要，让正文 Required Audit Answers 更精确地说明 files_changed 已补齐。
5. 如修改 pytest_result.txt，更新为当前 files_changed rework identity。
6. 重新运行并记录 required tests/status commands。
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
.codex-skills/registry.json

project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
```

必要时读取：

```text
tests/test_project_state.py
reverse_agent/project_state.py
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse 样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 engineering_branch？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不解新题？
5. 是否确认未推进 cpp2_883e67b9？
6. 是否确认本轮只修 report metadata/files_changed/pytest_result？
7. codex_report_summary.files_changed 是否已包含 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json？
8. codex_report_summary.files_changed 是否仍包含 project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json？
9. codex_report_summary.generated_artifacts 是否仍包含两个 rework artifact？
10. 正文 Required Audit Answers 是否与顶部 summary 一致？
11. pytest_result 是否绑定当前 files_changed rework decision/report/round？如果未修改 pytest_result，请说明原因。
12. 是否重新运行 lint-decision？结果是什么？
13. 是否重新运行 lint-report？结果是什么？
14. 是否重新运行 project_state status？结果是什么？
15. 是否重新运行 git diff --check？结果是什么？
16. 是否记录 git status --short 和 git diff --name-status？
17. 是否没有运行样本？
18. 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？
19. 是否没有调用 IDA/Ghidra 或读取二进制？
20. 是否没有修改 training_status/status_overlay？
21. 是否没有读取 full solve_reports？
22. 是否没有修改 solver production code？如果有，为什么必须修改？
23. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — fix codex_report_summary.files_changed

修正 `project_state/codex_execution_report.md` 顶部 `codex_report_summary`。

必须使用当前 files_changed rework identity：

```text
report_id=report_20260608_solver_profile_dispatch_files_changed_rework_v1
round_id=round_20260608_solver_profile_dispatch_files_changed_rework_v1
based_on_decision_id=decision_20260608_solver_profile_dispatch_files_changed_rework_v1
mainline=engineering_branch
sample_id=multi_solved_profile_dispatch_files_changed_rework
```

`files_changed` 至少包含：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/artifact_index.json
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
```

如果本轮实际没有修改 `project_state/pytest_result.txt` 或 `project_state/artifact_index.json`，可以在正文中解释“上一轮已修改/本轮未新增修改”；但顶部 `files_changed` 必须满足本轮审计要求，不能再漏列 `guardrails_report_rework_audit.json`。

### Phase B — keep generated_artifacts stable

`generated_artifacts` 必须继续包含：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
```

不要删除其中任一项。

### Phase C — repair pytest_result if needed

如果修改 `project_state/pytest_result.txt`，必须绑定当前 files_changed rework：

```text
decision_id=decision_20260608_solver_profile_dispatch_files_changed_rework_v1
report_id=report_20260608_solver_profile_dispatch_files_changed_rework_v1
round_id=round_20260608_solver_profile_dispatch_files_changed_rework_v1
status=PASSED|FAILED
```

必须记录每条命令的结果。若某条命令没有运行，不能写 PASS，也不能把 report 标为 SUCCESS/ACCEPTED。

### Phase D — do not change solver logic

默认不修改：

```text
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
```

如果测试失败迫使修改代码，必须停止并报告 REWORK_REQUIRED，不要在本轮扩张修复范围。

---

## 7. Tests

必须至少运行并记录：

```text
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议同时运行：

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
```

如果 Codex 报告继续声明 179 tests passed，则必须实际重跑并在 `project_state/pytest_result.txt` 记录完整 pytest 命令。不能沿用上一轮测试结论冒充本轮测试。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 无法读取上一轮两个 rework audit artifact，因此无法修正 files_changed/generated_artifacts。
3. codex_report_summary.files_changed 仍漏列 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json。
4. generated_artifacts 丢失任一 rework artifact。
5. pytest_result 无法绑定当前 files_changed rework decision/report/round，且报告却声称本轮测试已通过。
6. 无法运行 required lint/status commands。
7. 需要运行真实样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
8. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
9. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
10. 需要修改 solver production code 才能完成报告 metadata 一致性修复。
11. 正文 Required Audit Answers 与顶部 codex_report_summary 再次不一致。
```

完成后不要继续下一轮样本求解。下一步建议只能写入报告，不要自行扩大到 `tool_integration` 或 `reverse_solving`。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_report_consistency_rework_v1",
  "round_id": "round_20260608_solver_profile_dispatch_report_consistency_rework_v1",
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

目标：修复上一轮 `guardrails_report_rework` 的 Codex 报告 metadata 与正文不一致问题，使 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/artifact_index.json` 三者在当前 rework 轮次下可审计。

当前阻断点不是 solver 逻辑，也不是 guardrail 代码。上一轮已经修复了 guardrails audit artifact 的 sha256/size 记录，并补全了 `tests_ran` 的完整命令；但报告仍不可接受，原因是：

```text
1. codex_report_summary.files_changed 漏列新增的 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json。
2. codex_report_summary.generated_artifacts 为空，但上一轮实际生成并登记了 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json。
3. codex_execution_report.md 正文仍保留过期的 “lint-report: FAILED / 修复后将重新验证” 表述，与 summary 的 SUCCESS/ACCEPTED 和 pytest_result 的 PASS 冲突。
```

本轮只修 report metadata / report text / pytest_result 最终记录。不要改 solver 逻辑，不要改测试逻辑，不推进样本求解。

必须完成：

```text
1. 把 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json 加入 codex_report_summary.files_changed。
2. 把 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json 加入 codex_report_summary.generated_artifacts。
3. 删除或改写 codex_execution_report.md 正文中所有过期的 lint-report FAILED / 修复后将重新验证 表述。
4. 确保正文、summary、pytest_result 对 lint-report 的最终结论一致：PASS。
5. 重新运行并记录 required tests/status commands。
6. 如本轮修改 pytest_result.txt，必须绑定当前 consistency rework decision/report/round。
```

建议产出：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可选产出：

```text
project_state/artifact_index.json  # 仅当需要登记本轮新的 audit artifact 时修改
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json  # 可选；若生成必须登记 artifact_index
```

默认不要修改：

```text
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮被审计提交：

```text
commit=9e2a92a3fd7cad753452330abe310e3bbca7a9fe
message=rework: fix artifact provenance and report records for guardrails round
round=round_20260608_solver_profile_dispatch_guardrails_report_rework_v1
decision=decision_20260608_solver_profile_dispatch_guardrails_report_rework_v1
```

上一轮已完成的可接受部分：

```text
1. artifact_index 中 guardrails audit artifact 的空文件 hash e3b0c442... 已替换为 e7f467c16b46fb33c06447179bb6b9476767fc4d0f97276933a4ff6ca2b05cd9。
2. guardrails audit artifact size_bytes 已修正为 2382。
3. codex_report_summary.tests_ran 已列出 8 条完整命令。
4. pytest_result.txt 已记录 179 passed 和 lint-report PASS (after report update)。
5. diff 范围没有修改 solver production code。
```

上一轮仍不可接受的部分：

```text
1. codex_report_summary.files_changed 只列 project_state/artifact_index.json、project_state/codex_execution_report.md、project_state/pytest_result.txt，漏列新增的 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json。
2. codex_report_summary.generated_artifacts 是 []，但实际新增了 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json 并登记进 artifact_index。
3. codex_execution_report.md 正文仍写 lint-report FAILED / 修复后重新验证，而 pytest_result.txt 写 lint-report PASS。
4. GitHub Actions workflow_runs 为空，不能用远端 CI 代替 project_state 记录；因此 project_state 报告必须自洽。
```

当前 training summary 仍应保持不变：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver 和 project_state lint/status 机制。本轮只修 project_state 报告一致性，不调用成熟逆向工具，不重写反汇编/反编译/调试能力。

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
19. 不要保留 report 正文中的过期 lint-report FAILED 结论。
20. 不要让 summary/generated_artifacts 与实际新增 artifact 不一致。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮 report、pytest_result、artifact_index、rework audit artifact。
3. 修正 codex_execution_report.md 的 summary 和正文。
4. 修正 pytest_result.txt 绑定与命令记录。
5. 如生成本轮 consistency rework audit artifact，更新 artifact_index。
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
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
project_state/local_reverse_training_status.json
```

必要时读取：

```text
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
tests/test_project_state.py
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
6. 是否确认本轮只修 report metadata/report text/pytest_result？
7. files_changed 是否包含 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json？
8. generated_artifacts 是否包含 project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json？
9. codex_execution_report.md 正文是否已删除或改写所有过期 lint-report FAILED 表述？
10. summary、正文、pytest_result 对 lint-report 的最终结论是否均为 PASS？
11. pytest_result 是否绑定当前 consistency rework decision/report/round？
12. 是否重新运行 py_compile？
13. 是否重新运行 pytest？结果是多少？
14. 是否重新运行 lint-decision？
15. 是否重新运行 lint-report？
16. 是否重新运行 project_state status？
17. 是否重新运行 git diff --check？
18. 是否记录 git status --short 和 git diff --name-status？
19. 是否没有运行样本？
20. 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？
21. 是否没有调用 IDA/Ghidra 或读取二进制？
22. 是否没有修改 training_status/status_overlay？
23. 是否没有读取 full solve_reports？
24. 是否没有修改 solver production code？如果有，为什么必须修改？
25. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — fix codex_report_summary metadata

修正 `project_state/codex_execution_report.md` 顶部 `codex_report_summary`。

必须使用当前 consistency rework identity：

```text
report_id=report_20260608_solver_profile_dispatch_report_consistency_rework_v1
round_id=round_20260608_solver_profile_dispatch_report_consistency_rework_v1
based_on_decision_id=decision_20260608_solver_profile_dispatch_report_consistency_rework_v1
mainline=engineering_branch
sample_id=multi_solved_profile_dispatch_report_consistency_rework
```

`files_changed` 至少包含：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果本轮实际修改 `artifact_index.json` 或生成新的 consistency audit artifact，也必须列入 `files_changed`。

同时必须在 summary 的 `generated_artifacts` 中记录上一轮实际生成但漏报的 artifact：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
```

如果本轮又生成新的 artifact，也要一并记录。

### Phase B — fix stale body text

修正 `codex_execution_report.md` 正文：

```text
1. 不得保留 “lint-report: FAILED” 作为最终状态。
2. 不得保留 “修复后将重新验证” 之类过期未来式表述。
3. 可以说明上一轮曾因报告 ID 不匹配失败，但必须明确本轮最终重新运行后 lint-report=PASS。
4. Required Audit Answers 中 lint-report 行必须写 YES/PASS，不得写 FAILED。
5. Test Results / Lint Status 中 lint-report 必须写最终 PASS。
```

### Phase C — repair pytest_result

修正 `project_state/pytest_result.txt`，必须绑定当前 consistency rework：

```text
decision_id=decision_20260608_solver_profile_dispatch_report_consistency_rework_v1
report_id=report_20260608_solver_profile_dispatch_report_consistency_rework_v1
round_id=round_20260608_solver_profile_dispatch_report_consistency_rework_v1
status=PASSED|FAILED
```

必须记录每条命令的结果。若某条命令没有运行，不能写 PASS，也不能把 report 标为 SUCCESS/ACCEPTED。

### Phase D — artifact_index handling

默认不需要改上一轮 artifact_index，因为上一轮已经登记：

```text
local_reverse_solver_profile_dispatch_guardrails_report_rework_audit
```

只有在本轮生成新的 consistency rework audit artifact 时，才修改 `project_state/artifact_index.json` 并登记：

```text
local_reverse_solver_profile_dispatch_report_consistency_rework_audit
```

若登记新 artifact，必须包含真实 path、sha256、size_bytes、freshness=current、source_run 当前 round。

### Phase E — do not change solver logic

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
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`project_state/pytest_result.txt` 必须能证明这些命令真实运行，并绑定当前 consistency rework decision/report/round。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 无法读取上一轮 rework audit artifact，因此无法修正 files_changed/generated_artifacts。
3. codex_execution_report.md 中仍残留最终 lint-report FAILED 表述。
4. pytest_result 无法绑定当前 consistency rework decision/report/round。
5. 无法运行 required tests/status commands。
6. 需要运行真实样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
7. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
8. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
9. 需要修改 solver production code 才能完成报告一致性修复。
10. generated_artifacts 与实际新增 artifact 仍不一致。
```

完成后不要继续下一轮样本求解。下一步建议只能写入报告，不要自行扩大到 `tool_integration` 或 `reverse_solving`。

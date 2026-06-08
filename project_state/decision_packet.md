```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_guardrails_report_rework_v1",
  "round_id": "round_20260608_solver_profile_dispatch_guardrails_report_rework_v1",
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

目标：返工上一轮 `solver_profile_dispatch_guardrails` 的状态记录与审计 provenance，使 project_state 可审计、可接受。

上一轮代码方向不要求重写；当前阻断点不是 solver guardrail 思路，而是状态记录不可信：

```text
1. artifact_index.latest_artifacts_v2["local_reverse_solver_profile_dispatch_guardrails_audit"].sha256 记录为 e3b0c442...，这是空文件 hash，但同一条记录 size_bytes=1789，明显不一致。
2. codex_execution_report.md 顶部 codex_report_summary.tests_ran 只列出测试文件名，没有列出实际运行命令；decision 要求 py_compile、pytest、lint-decision、lint-report、project_state status、git diff/status/name-status 都必须记录。
```

本轮只修复 report/provenance/test record。除非重新运行测试暴露 guardrail 行为失败，否则不要改 solver 逻辑。

必须完成：

```text
1. 重新计算 project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json 的真实 sha256。
2. 修正 artifact_index.latest_artifacts_v2 中该 artifact 的 sha256，使其与文件内容一致。
3. 确认 size_bytes 与 artifact 文件实际大小一致；如不一致必须修正。
4. 修正 codex_execution_report.md 顶部 codex_report_summary.tests_ran，列出完整实际运行命令。
5. 确认 pytest_result.txt 绑定当前 rework decision/report/round。
6. 重新运行并记录 required tests/status commands。
```

建议产出：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json  # 只在需要补字段或修正内容时修改
```

不要修改 `reverse_agent/local_reverse_constraint_recovery.py`、`reverse_agent/local_reverse_solver_profiles.py` 或测试文件，除非重新运行测试发现 guardrail 行为确实失败；如果修改代码，必须在报告中明确说明触发原因。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮被审计的提交：

```text
commit=bf0329aa06fa94ffa3ac64515534e2ccf4ed8ae7
message=guardrail: profile/classification mismatch and freshness=current checks for solver profile dispatch
round=round_20260608_solver_profile_dispatch_guardrails_v1
decision=decision_20260608_solver_profile_dispatch_guardrails_v1
```

上一轮提交声称完成：

```text
- Add PROFILE_CLASSIFICATION_MISMATCH guardrail
- Add NON_CURRENT_PROFILE_EVIDENCE guardrail
- Check top-level and nested normalized_profile_evidence profile against classification
- Enforce freshness=current; block stale/missing/unknown/empty
- Add 7 synthetic-only tests
- All 179 tests pass, lint-decision PASS, lint-report PASS
```

上一轮 diff 范围：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
project_state/pytest_result.txt
reverse_agent/local_reverse_constraint_recovery.py
tests/test_local_reverse_solver_profile_dispatch.py
```

审计结论为 **REWORK_REQUIRED**，原因：

```text
1. artifact_index 中 guardrails audit artifact 的 sha256 是 e3b0c44298fc...，即空文件 hash；但记录 size_bytes=1789，provenance 不可信。
2. codex_report_summary.tests_ran 不完整，只列测试文件名，未记录完整实际命令。
3. GitHub Actions workflow_runs 为空，combined status 无 checks；因此不能用远端 CI 代替 project_state 测试记录。
```

当前 training summary 仍应保持不变：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver 和 project_state lint/status 机制。本轮只修 project_state 记录与审计 provenance，不调用成熟逆向工具，不重写反汇编/反编译/调试能力。

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
18. 不要改 solver 逻辑来掩盖报告/provenance 问题。
19. 不要保留 e3b0c442... 作为非空 audit artifact 的 sha256。
20. 不要在 codex_report_summary.tests_ran 中只写测试文件名；必须写完整命令。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮 guardrails report、pytest_result、artifact_index、audit artifact。
3. 读取相关源码和测试以确认无需改代码。
4. 重新计算 audit artifact hash 和 size。
5. 修正 artifact_index 注册项。
6. 修正 codex_execution_report.md 和 pytest_result.txt。
7. 重新运行并记录 required tests/status commands。
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

project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
project_state/local_reverse_solver_profile_dispatch_integration_audit.json
project_state/local_reverse_training_status.json

reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runtime.py
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
6. 是否确认本轮只修 report/provenance/test record？
7. guardrails audit artifact 的真实 sha256 是什么？
8. artifact_index 中记录的 sha256 是否与真实文件一致？
9. artifact_index 中 size_bytes 是否与真实文件一致？
10. 是否移除了错误的 e3b0c442 空文件 hash？
11. codex_report_summary.tests_ran 是否列出完整命令？
12. pytest_result 是否绑定当前 rework decision/report/round？
13. 是否重新运行 py_compile？
14. 是否重新运行 pytest？结果是多少？
15. 是否重新运行 lint-decision？
16. 是否重新运行 lint-report？
17. 是否重新运行 project_state status？
18. 是否重新运行 git diff --check？
19. 是否记录 git status --short 和 git diff --name-status？
20. 是否没有运行样本？
21. 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？
22. 是否没有调用 IDA/Ghidra 或读取二进制？
23. 是否没有修改 training_status/status_overlay？
24. 是否没有读取 full solve_reports？
25. 是否没有修改 solver production code？如果有，为什么必须修改？
26. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — repair artifact provenance

必须重新计算：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
```

并修正：

```text
project_state/artifact_index.json
```

要求：

```text
1. latest_artifacts["local_reverse_solver_profile_dispatch_guardrails_audit"] 路径正确。
2. latest_artifacts_v2["local_reverse_solver_profile_dispatch_guardrails_audit"].sha256 等于真实文件 sha256。
3. latest_artifacts_v2["local_reverse_solver_profile_dispatch_guardrails_audit"].size_bytes 等于真实文件大小。
4. freshness=current 只能在 path、sha256、size_bytes 都一致时保留。
5. artifact_refs["local_reverse_solver_profile_dispatch_guardrails_audit"] 路径正确。
6. 不要删除或覆盖上一轮 integration audit 和 engineering recovery audit。
```

### Phase B — repair report summary

修正 `project_state/codex_execution_report.md` 顶部 `codex_report_summary`。

必须使用当前 rework identity：

```text
report_id=report_20260608_solver_profile_dispatch_guardrails_report_rework_v1
round_id=round_20260608_solver_profile_dispatch_guardrails_report_rework_v1
based_on_decision_id=decision_20260608_solver_profile_dispatch_guardrails_report_rework_v1
mainline=engineering_branch
sample_id=multi_solved_profile_dispatch_guardrails_report_rework
```

`tests_ran` 必须列出完整命令，而不是只列测试文件名：

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

`files_changed` 应只包含真实改动文件，例如：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json  # 仅当实际修改
```

如果 solver/test 文件未改，不要列入 `files_changed`。

### Phase C — repair pytest_result

修正 `project_state/pytest_result.txt`，必须绑定当前 rework：

```text
decision_id=decision_20260608_solver_profile_dispatch_guardrails_report_rework_v1
report_id=report_20260608_solver_profile_dispatch_guardrails_report_rework_v1
round_id=round_20260608_solver_profile_dispatch_guardrails_report_rework_v1
status=PASSED|FAILED
```

必须记录每条命令的结果。若某条命令没有运行，不能写 PASS，也不能把 report 标为 SUCCESS/ACCEPTED。

### Phase D — do not change solver logic unless tests fail

默认不修改：

```text
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
```

只有当重新运行测试发现 guardrail 行为失败时，才允许最小代码修复。若发生这种情况，报告必须列出失败测试、原因、最小修复范围，并继续遵守“不运行样本/不做 runtime validation”。

### Phase E — optional rework audit artifact

可以生成一个轻量 rework audit artifact：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
```

如果生成，必须登记到 artifact_index，并包含：

```text
schema_version
generated_at
mainline=engineering_branch
round_id=round_20260608_solver_profile_dispatch_guardrails_report_rework_v1
decision_id=decision_20260608_solver_profile_dispatch_guardrails_report_rework_v1
source_failed_report=report_20260608_solver_profile_dispatch_guardrails_v1
source_failed_commit=bf0329aa06fa94ffa3ac64515534e2ccf4ed8ae7
issues_repaired
artifact_sha256_before
audit_artifact_sha256_after
audit_artifact_size_bytes_after
report_tests_ran_repaired=true
runtime_actions_performed=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
full_solve_reports_read=false
sample_binary_read=false
ida_or_ghidra_invoked=false
debugger_hook_emulator_probe_winpty_used=false
production_code_modified=false  # 或 true + reason
```

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

`project_state/pytest_result.txt` 必须能证明这些命令真实运行，并绑定当前 rework decision/report/round。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 无法读取 guardrails audit artifact，因此无法计算真实 sha256/size。
3. artifact_index 无法修正 sha256/size/freshness provenance。
4. pytest_result 无法绑定当前 rework decision/report/round。
5. 无法运行 required tests/status commands。
6. 需要运行真实样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
7. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
8. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
9. 需要把真实 candidate 写进 production code 才能通过测试。
10. 发现 solver guardrail 逻辑本身失败，且无法在本轮小范围修复。
```

完成后不要继续下一轮样本求解。下一步建议只能写入报告，不要自行扩大到 `tool_integration` 或 `reverse_solving`。

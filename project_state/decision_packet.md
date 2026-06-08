```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1",
  "round_id": "round_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1",
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

目标：修复上一轮 `files_changed_rework` 的最后一个 report metadata 不一致问题。

当前阻断点很窄：`decision_packet.md` 要求 `codex_report_summary.files_changed` 至少包含 `project_state/artifact_index.json`，但当前 `codex_execution_report.md` 顶部 summary 没有列它。上一轮已经修掉 `guardrails_report_rework_audit.json` 漏列问题，但还漏了 `artifact_index.json`。

本轮只允许修：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt  # 如果需要更新本轮测试记录
```

不要改：

```text
reverse_agent/
tests/
project_state/artifact_index.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 report 已绑定：

```text
report_20260608_solver_profile_dispatch_files_changed_rework_v1
round_20260608_solver_profile_dispatch_files_changed_rework_v1
decision_20260608_solver_profile_dispatch_files_changed_rework_v1
```

上一轮已完成的可接受部分：

```text
1. codex_report_summary.files_changed 已包含：
   - project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
   - project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
2. generated_artifacts 仍保留两个 rework artifact。
3. pytest_result.txt 已绑定 files_changed rework，并记录 status=PASSED。
4. lint-decision PASS、lint-report PASS、project_state status PASS、git diff --check PASS。
5. 未运行样本，未调用 IDA/Ghidra/debugger/hook/probe/winpty，未改 solver production code。
```

上一轮仍不可接受的部分：

```text
codex_report_summary.files_changed 缺少：
project_state/artifact_index.json
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
1. 不要推进 cpp2_883e67b9。
2. 不要运行任何 E:\reverse 样本。
3. 不要运行 candidate / negative control / runtime validation。
4. 不要 attach debugger / hook / emulator / probe / winpty。
5. 不要调用 IDA/Ghidra 或读取样本二进制。
6. 不要 brute force、dictionary search、fuzz、扩大预算。
7. 不要修改 solver production code。
8. 不要修改测试逻辑。
9. 不要修改 training_status 或 status_overlay。
10. 不要修改 project_state/artifact_index.json。
11. 不要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
12. 不要提交 full solve_reports。
13. 不要把 task_packet.task 当执行权威。
14. 不要删除 generated_artifacts 中已经正确列出的两个 artifact。
15. 不要让正文 Required Audit Answers 与顶部 codex_report_summary 再次不一致。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮 report、pytest_result、artifact_index、两个 rework audit artifact。
3. 修正 codex_execution_report.md 的 summary files_changed。
4. 如需要，让正文 Required Audit Answers 更精确地说明 artifact_index.json 已列入 files_changed。
5. 如修改 pytest_result.txt，更新为当前 artifact_index_files_changed_rework identity。
6. 重新运行并记录 required lint/status commands。
```

---

## 4. Files To Inspect

必须读取：

```text
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/artifact_index.json
project_state/task_packet.json
project_state/negative_results.json
.codex-skills/registry.json
```

必要时读取：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不要读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
E:\reverse 样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 engineering_branch？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving？
5. 是否确认没有推进 cpp2_883e67b9？
6. 是否只修 codex_execution_report / pytest_result？
7. codex_report_summary.files_changed 是否已包含 project_state/artifact_index.json？
8. files_changed 是否仍包含两个 rework audit artifact？
9. generated_artifacts 是否仍保留两个 rework artifact？
10. pytest_result 是否绑定当前 artifact_index_files_changed_rework identity？
11. 是否重新运行 lint-decision？
12. 是否重新运行 lint-report？
13. 是否重新运行 project_state status？
14. 是否重新运行 git diff --check？
15. 是否记录 git status --short 和 git diff --name-status？
16. 是否没有运行样本、IDA/Ghidra、debugger、hook、probe、winpty？
17. 是否没有修改 solver / tests / training status / status overlay / artifact_index？
18. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — 修 codex_report_summary.files_changed

把 `project_state/codex_execution_report.md` 顶部 identity 改为本轮：

```text
report_id=report_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
round_id=round_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
based_on_decision_id=decision_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
mainline=engineering_branch
sample_id=multi_solved_profile_dispatch_artifact_index_files_changed_rework
```

`files_changed` 必须至少包含：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/artifact_index.json
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
```

如果本轮实际没有修改 `project_state/artifact_index.json`，可以在正文说明它是上一轮已修改/本轮未新增修改；但顶部 summary 必须按本轮审计要求列入该路径，不能再漏列。

### Phase B — 保持 generated_artifacts 不变

`generated_artifacts` 必须继续包含：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_report_rework_audit.json
project_state/local_reverse_solver_profile_dispatch_report_consistency_rework_audit.json
```

不要删除。

### Phase C — 更新 pytest_result

如果本轮修改 `project_state/pytest_result.txt`，必须绑定当前轮：

```text
decision_id=decision_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
report_id=report_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
round_id=round_20260608_solver_profile_dispatch_artifact_index_files_changed_rework_v1
status=PASSED|FAILED
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

不要求跑完整 pytest。除非 Codex 报告继续写 “179 passed”，否则不要沿用上一轮完整测试结果。

---

## 8. Stop Conditions

出现以下任一情况立即停止并报告 `REWORK_REQUIRED`：

```text
1. files_changed 仍缺 project_state/artifact_index.json。
2. generated_artifacts 丢失任一 rework artifact。
3. pytest_result 没有绑定当前轮 identity，却声称本轮测试通过。
4. 需要修改 solver / tests 才能通过。
5. 需要运行样本、IDA/Ghidra、debugger、hook、probe、winpty。
6. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
7. 正文 Required Audit Answers 与顶部 summary 再次不一致。
8. git diff 包含允许范围外文件。
```

完成后不要继续下一轮样本求解。当前任务只收口 report metadata。

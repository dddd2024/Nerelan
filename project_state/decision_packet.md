```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_7b504c54_static_triage_report_rework_v1",
  "round_id": "round_20260605_cpp1_7b504c54_static_triage_report_rework_v1",
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

目标：修复上一轮 `decision_20260605_cpp1_7b504c54_static_triage_v1` 的报告/测试记录一致性问题。上一轮静态分诊 artifact 本身已经生成，且 `artifact_index.json` 已登记 current artifact；本轮不得重新推进样本分析，不重新运行 IDA，不继续求解 `cpp1_7b504c54`。

需要修复的核心问题：

```text
1. `pytest_result.txt` 中 `lint-report` 实际 Exit Code=1，却被标记为 EXPECTED_MISMATCH / PASSED。
2. `project_state status` 显示 decision_ready_for_execution=True、decision_execution_state=READY_FOR_EXECUTION、decision_consumed_by_report=False。
3. `codex_execution_report.md` 却写 status=SUCCESS、acceptance_recommendation=ACCEPTED，和状态事实矛盾。
4. `.gitignore` 被加入 `project_state/triage_*/`，但上一轮 decision 的 allowed files 没有显式允许 `.gitignore`，需要回退或明确记录为越界但合理的 artifact hygiene 变更。
```

本轮只允许修复 active report / pytest 记录，使当前 decision 被当前 SUCCESS report 消费，或在无法修复时把 report 标记为 BLOCKED/REWORK_REQUIRED。

不得修改或重新生成：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

当前 `current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 static triage artifact 已存在：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
sample_id=cpp1_7b504c54
analysis_mode=single_sample_static_triage
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
tool_status=success
source_tool=IDA
candidate=null
known_candidate=""
```

上一轮 artifact_index 已登记：

```text
artifact key=local_reverse_cpp1_7b504c54_static_triage
kind=local_reverse_single_sample_static_triage
path=project_state\local_reverse_cpp1_7b504c54_static_triage.json
freshness=current
source_run=round_20260605_cpp1_7b504c54_static_triage_v1
sample_id=cpp1_7b504c54
```

上一轮 `codex_execution_report.md` 存在不一致：

```text
status=SUCCESS
acceptance_recommendation=ACCEPTED
test_results.lint_report=EXPECTED_MISMATCH
test_results.project_state_status=PASSED (Exit code 0; decision_ready_for_execution=True)
```

上一轮 `pytest_result.txt` 明确显示：

```text
lint-report Exit Code: 1
lint-report: FAILED
error: based_on_decision_id does not match current decision_id
error: report round_id does not match current decision round_id
Result: EXPECTED_MISMATCH

project_state status:
decision_ready_for_execution=True
decision_execution_state=READY_FOR_EXECUTION

summary:
decision_consumed_by_report=False
decision_execution_state=READY_FOR_EXECUTION
```

这不能作为通过测试接受。必须重新生成本轮 report/pytest，使：

```text
lint-report: OK
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

`.gitignore` 当前包含：

```text
# IDA triage temp directories
project_state/triage_*/
```

该变更在上一轮有合理动机：避免提交 IDA temp directories。但上一轮 decision 未允许修改 `.gitignore`，本轮必须二选一：

```text
1. 回退 `.gitignore` 改动；
2. 保留 `.gitignore` 改动，但在 report 中明确标记为 artifact hygiene 变更，并说明它是上一轮 scope 越界但安全合理的修正。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
6. run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 IDA。
2. 不重新运行 `local_reverse_single_sample_static_triage` CLI，除非只是只读验证且不改 artifact；默认不运行。
3. 不动态执行样本。
4. 不做 runtime validation。
5. 不运行 debugger/runtime probe/hook/emulator。
6. 不运行 solver/bruteforce/guided pool/constraint recovery。
7. 不生成 candidate。
8. 不写 known_candidate。
9. 不标记 solved。
10. 不修改 `project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
11. 不修改 `project_state/artifact_index.json`。
12. 不修改 `project_state/local_reverse_training_status.json`。
13. 不修改 `project_state/local_reverse_evaluation_queue.json`。
14. 不修改 `reverse_agent/local_reverse_single_sample_static_triage.py`。
15. 不修改 `tests/test_local_reverse_single_sample_static_triage.py`。
16. 不修改 `.codex-skills`。
17. 不提交本地 binary、IDA sidecar、raw temp、`project_state/triage_*` 或 full solve_reports。
18. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
19. 不把 `lint-report Exit Code 1` 标成通过。
20. 不在 `decision_consumed_by_report=False` 时写 SUCCESS/ACCEPTED。
```

允许：

```text
1. 修改 `project_state/codex_execution_report.md`。
2. 修改 `project_state/pytest_result.txt`。
3. 按二选一策略修改 `.gitignore`：要么回退上一轮改动，要么保留并在 report 中明确记录为 artifact hygiene scope exception。
4. 只读检查 `project_state/local_reverse_cpp1_7b504c54_static_triage.json` 和 `project_state/artifact_index.json`。
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
project_state/local_reverse_cpp1_7b504c54_static_triage.json
.gitignore
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 engineering_branch。
4. 是否确认本轮只修复 report/pytest 一致性。
5. 是否确认未重新运行 IDA 或 static triage。
6. 是否确认没有动态执行样本，没有 runtime validation。
7. 是否确认没有 solver/bruteforce/guided pool/constraint recovery。
8. 是否确认没有写 candidate / known_candidate。
9. 是否确认没有标记 solved。
10. 是否确认未修改 `local_reverse_cpp1_7b504c54_static_triage.json`。
11. 是否确认未修改 `artifact_index.json`。
12. 是否确认未修改 training_status / evaluation_queue。
13. 是否说明 `.gitignore` 处理策略：回退，或保留并标记为 artifact hygiene scope exception。
14. 是否确认 `codex_report_summary.generated_artifacts` 包含本轮实际生成/重写的文件。
15. 是否确认 `pytest_result.txt` 重新记录当前 report 状态。
16. 是否确认 `lint-report` Exit Code=0 且输出 OK。
17. 是否确认 `project_state status` 显示 decision_consumed_by_report=True。
18. 是否确认 `decision_execution_state=CONSUMED_BY_SUCCESS_REPORT`。
19. 是否确认 `git status --short` 和 `git diff --name-status` 只包含允许文件。
20. 如果任何一条不满足，report status 不得为 SUCCESS，acceptance_recommendation 不得为 ACCEPTED。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

按需允许修改：

```text
.gitignore
```

但 `.gitignore` 必须二选一处理：

```text
1. 回退上一轮加入的 `project_state/triage_*/`；
2. 或保留，并在 report 的 Scope Audit 中写明：`.gitignore` was retained as an artifact hygiene scope exception to prevent IDA temp directories from entering Git.
```

不得修改：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
reverse_agent/local_reverse_single_sample_static_triage.py
tests/test_local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
.codex-skills/*
solve_reports/*
project_state/triage_*
```

本轮 `codex_report_summary` 建议：

```text
report_id=report_20260605_cpp1_7b504c54_static_triage_report_rework_v1
round_id=round_20260605_cpp1_7b504c54_static_triage_report_rework_v1
based_on_decision_id=decision_20260605_cpp1_7b504c54_static_triage_report_rework_v1
status=SUCCESS only if lint-report/status now pass and decision is consumed
acceptance_recommendation=ACCEPTED only if status=SUCCESS and all required tests pass
generated_artifacts=["project_state/codex_execution_report.md", "project_state/pytest_result.txt"]
```

如果 `.gitignore` 被修改或保留为 scope exception，必须列入 `files_changed`，但不要列入 `generated_artifacts`。

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED 结果；
5. 本轮 decision_id、round_id、report_id。
```

硬性通过条件：

```text
lint-report Exit Code=0
lint-report: OK
project_state status Exit Code=0
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
decision_ready_for_execution=False
```

如果这些条件不满足，则本轮 report 必须为 BLOCKED 或 REWORK_REQUIRED。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. 当前 active decision/report/pytest 无法解析。
2. 重新生成 report 后 `lint-report` 仍然 Exit Code=1。
3. `project_state status` 仍显示 decision_consumed_by_report=False。
4. `project_state status` 仍显示 decision_execution_state=READY_FOR_EXECUTION。
5. 需要修改 static triage artifact 或 artifact_index 才能通过。
6. 需要重新运行 IDA 或 static triage 才能通过。
7. 需要动态执行样本或 runtime probe。
8. 需要 solver/bruteforce/candidate generation。
9. git diff 包含本轮 forbidden files。
```

成功完成的最低标准：

```text
1. 当前 active report 消费本轮 decision。
2. lint-report OK。
3. project_state status 显示 decision_consumed_by_report=True。
4. pytest_result 不再把 Exit Code 1 标成通过。
5. report 明确说明本轮没有重新推进样本分析，只修复 report/pytest 一致性。
6. `.gitignore` 处理策略被明确记录。
```

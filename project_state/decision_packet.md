```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_report_summary_generated_artifacts_schema_fix_v1",
  "round_id": "round_20260605_report_summary_generated_artifacts_schema_fix_v1",
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

目标：修复上一轮审计发现的 `CODEX_EXECUTION_REPORT` schema 完整性问题。上一轮功能实现可接受，但 `project_state/codex_execution_report.md` 顶部的 `codex_report_summary` 缺少项目规范要求的 `generated_artifacts` 字段；同时 `python -m reverse_agent.project_state lint-report --state-dir project_state` 没有拦截该缺失字段。

本轮只做报告 schema 和 lint/test 层面的工程修复：

```text
1. 补全当前 `project_state/codex_execution_report.md` 的 `codex_report_summary.generated_artifacts` 字段。
2. 更新 `reverse_agent/project_state.py` 的 lint-report/schema 校验，使 SUCCESS/PARTIAL/BLOCKED/FAILED 报告的 `codex_report_summary` 必须显式包含 `generated_artifacts`。
3. 更新 `tests/test_project_state.py`，增加缺少 `generated_artifacts` 时 lint-report 应失败或至少返回非 OK 的测试。
4. 重新运行 project_state lint/status，确保当前 report 被当前 decision 消费。
```

本轮不得推进任何逆向样本、训练集队列、solver、IDA/Ghidra/debugger 接入或 runtime probe。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮；其 `execution_scope=decision_packet_controls_current_round`，并且 `local_reverse_task_packet_authority_note` 明确 `project_state/decision_packet.md` 才是执行权威。

当前 `current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id` 为：

```text
state_20260602_053948_4e3984041cd7
```

`based_on_state_digest` 为：

```text
4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 `decision_20260605_training_status_static_blocked_overlay_rework_v1` 已完成并通过功能审计，但结论为 `ACCEPTED_WITH_LIMITATIONS`，限制项为：

```text
codex_report_summary 缺少 generated_artifacts 字段。
lint-report 没有拦截该 schema 缺失。
```

当前 `project_state/codex_execution_report.md` 的 `codex_report_summary` 包含：

```text
schema_version
report_id
round_id
based_on_decision_id
status
acceptance_recommendation
files_changed
tests_ran
test_results
```

但缺少：

```text
generated_artifacts
```

上一轮实际重新生成了以下状态/训练集输出文件，应该进入 `generated_artifacts`：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
```

上一轮 `pytest_result.txt` 显示：

```text
status=PASSED
Total Commands=9
Passed=9
Failed=0
lint-report: OK
warning: report round not archived yet
generated_artifacts_count=0
```

这说明当前 lint-report 对 `generated_artifacts` 字段缺失没有硬性约束，是本轮需要修复的工程问题。

当前 `artifact_index.json` 中 `cpp1_2f6fcb63` 相关 artifacts 均为 current，包括 `local_reverse_cpp1_2f6fcb63_target_provenance_recheck`。这些只是背景证据，本轮不得修改这些 artifacts，也不得继续求解 `cpp1_2f6fcb63`。

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

现有相关能力：

```text
reverse_agent/project_state.py 已包含 lint-decision、lint-report、status 相关逻辑。
tests/test_project_state.py 已覆盖 project_state lint/status 行为。
.codex-skills/registry.json 中 active skill 只有 reverse-agent-iteration@v2 与 samplereverse-frontier@v2；本轮使用 reverse-agent-iteration@v2。
```

---

## 3. Do Not Do

严禁：

```text
1. 不推进 reverse_solving。
2. 不推进 training_dataset 输出逻辑。
3. 不修改 `local_reverse_training_status.py`，除非测试暴露与 report schema 直接相关的问题。
4. 不修改 `project_state/local_reverse_training_status.json`。
5. 不修改 `project_state/local_reverse_evaluation_queue.json`。
6. 不修改 `training_materials/local_reverse/status_overlay.json`。
7. 不修改 `artifact_index.json`。
8. 不修改任何 cpp1 static/recheck artifact。
9. 不运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
10. 不动态执行任何样本。
11. 不运行 solver/bruteforce/guided pool。
12. 不写 candidate / known_candidate。
13. 不标记任何样本 solved。
14. 不提交 solve_reports、原始样本、IDA sidecar、raw temp、本地绝对路径。
15. 不修改 `.codex-skills`。
16. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
17. 不把 task_packet.task 当执行权威。
```

允许：

```text
1. 修改 `reverse_agent/project_state.py` 的 report summary schema/lint 逻辑。
2. 修改 `tests/test_project_state.py`，补齐 generated_artifacts schema 测试。
3. 修改 `project_state/codex_execution_report.md`，补上 generated_artifacts 字段，并使它对应当前 engineering report。
4. 修改 `project_state/pytest_result.txt`，记录本轮真实测试命令和结果。
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
reverse_agent/project_state.py
tests/test_project_state.py
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 engineering_branch。
4. 是否确认本轮只修复 report schema/lint/test，不推进样本求解或训练集状态逻辑。
5. 是否确认没有运行 IDA/Ghidra/debugger/runtime probe/hook/emulator。
6. 是否确认没有动态执行样本。
7. 是否确认没有运行 solver/bruteforce/guided pool。
8. 是否确认没有写 candidate / known_candidate。
9. 是否确认没有修改 artifact_index 或任何 cpp1 artifact。
10. 是否确认 `codex_report_summary` 包含 `generated_artifacts` 字段。
11. 是否确认 `generated_artifacts` 至少列出本轮真正生成/重写的输出；如果本轮只修改 report/pytest，则必须说明哪些是 generated vs modified。
12. 是否确认上一轮实际生成的三个状态文件在补充说明中被记录：`project_state/local_reverse_training_status.json`、`project_state/local_reverse_evaluation_queue.json`、`training_materials/local_reverse/status_overlay.json`。
13. 是否确认 lint-report 在缺少 `generated_artifacts` 时会失败或给出不可接受状态。
14. 是否确认 tests 覆盖缺失 `generated_artifacts` 的 report summary。
15. 是否确认 `pytest_result.txt` 记录每条命令、Exit Code 和输出摘要。
16. 是否确认 `git status --short` 和 `git diff --name-status` 只包含允许文件。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/artifact_index.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
reverse_agent/local_reverse_training_status.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
.codex-skills/*
solve_reports/*
```

实现要求：

```text
1. `codex_report_summary` schema 必须要求字段：schema_version、report_id、round_id、based_on_decision_id、status、acceptance_recommendation、files_changed、tests_ran、generated_artifacts。
2. `generated_artifacts` 必须是 list。
3. 对 SUCCESS/PARTIAL/BLOCKED/FAILED report，缺失 `generated_artifacts` 应导致 lint-report 非 OK 或退出非 0。
4. `generated_artifacts` 可以为空 list，但字段必须显式存在；如果为空，报告正文必须说明没有生成 artifact。
5. 当前修复后的 report summary 应包含本轮实际 generated_artifacts。建议本轮将 `generated_artifacts` 设置为 `["project_state/codex_execution_report.md", "project_state/pytest_result.txt"]`，并在正文中说明上一轮生成的三个状态文件已被追认记录，不在本轮重新生成。
6. 不要把 modified source/test 文件放进 generated_artifacts，除非确实是生成产物。
7. `lint-report` 输出摘要应能显示 generated_artifacts_count。
8. 保持兼容旧 archived report 的读取；但当前 active report 必须符合新 schema。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/project_state.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增更细粒度测试文件，必须同时运行对应 pytest 命令并记录。

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 当前 active decision/report/pytest 无法解析。
2. 修改 lint-report 会破坏现有 active decision/report/status 流程，且无法用测试约束。
3. 需要读取 full solve_reports 或 PROJECT_PROGRESS_LOG 才能继续。
4. 需要修改训练集状态文件、artifact_index 或 cpp1 artifacts 才能通过测试。
5. 需要运行任何逆向工具、动态调试或样本执行。
6. 无法让 lint-report 对缺少 generated_artifacts 的 active report 产生失败/不可接受结果。
```

成功完成的最低标准：

```text
1. 当前 codex_report_summary 显式包含 generated_artifacts。
2. lint-report 对当前 active report 通过。
3. 新测试覆盖缺失 generated_artifacts 的 report summary。
4. project_state status 显示当前 decision 被当前 SUCCESS report 消费。
5. git diff 只包含 project_state report/pytest 与 project_state lint/test 相关文件。
```

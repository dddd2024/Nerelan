```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_cleanup_lint_report_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_cleanup_lint_report_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **tool_integration**。

目标：修复 cleanup 轮的测试记录矛盾。上一轮已经正确删除根目录工具 dump，但 `pytest_result.txt` 和 `codex_execution_report.md` 中同时出现 `status=PASSED / All checks passed` 与 `lint-report: FAILED`，违反审计规则。本轮只重新运行并记录通过的 lint-report/status 结果，不重新分析样本，不运行 IDA/Ghidra，不生成 candidate，不做 runtime validation。

必须完成：

```text
1. 保持 4 个根目录 JSON 工具 dump 已删除：
   - ida_evidence.json
   - sub_401014_key_init_analysis.json
   - sub_401120_analysis.json
   - xref_boundary_audit.json

2. 重新运行 lint-report，必须得到 OK / PASS。
3. 更新 project_state/pytest_result.txt，使其不再出现 lint-report FAILED。
4. 更新 project_state/codex_execution_report.md，使 Tests 表不再记录 lint-report FAILED。
5. 确认 codex_report_summary.files_changed 与实际 git diff --name-status 一致。
6. 保持 candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false。
```

本轮不得进入 reverse_solving。不得生成 candidate、不得验证 candidate、不得运行样本交互逻辑、不得 attach debugger/hook/probe/winpty/emulator、不得 brute force、不得 runtime validation、不得继续 IDA/Ghidra/static extraction。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED，原因是：

```text
1. 根目录 JSON 工具 dump 删除方向正确。
2. codex_execution_report.md 已绑定 cleanup decision。
3. pytest_result.txt 已绑定 cleanup decision。
4. 但 report/pytest_result 均记录 lint-report FAILED。
5. 同时 pytest_result 顶部写 status=PASSED，底部写 All checks passed，形成测试记录自相矛盾。
6. 没有 GitHub Actions 可作为外部通过佐证。
```

已完成且应保持：

```text
1. 根目录 JSON 工具 dump 已从仓库中删除。
2. project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json 无需修改。
3. project_state/artifact_index.json 无需修改。
4. 不生成 candidate，不 runtime validation。
```

需要修复：

```text
1. lint-report 必须重新运行并通过。
2. codex_execution_report.md 和 pytest_result.txt 必须记录通过结果。
3. 不得再出现 FAILED 与 PASSED 并存的矛盾记录。
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复旧 samplereverse 失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving。
2. 不要生成 candidate、验证 candidate、运行 negative control 或 runtime validation。
3. 不要运行样本交互逻辑。
4. 不要 attach debugger / hook / emulator / probe / winpty。
5. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
6. 不要继续执行 IDA/Ghidra/static extraction。
7. 不要新增更多 IDA/Ghidra/debugger/runtime/probe 接口。
8. 不要提交根目录工具 dump。
9. 不要把 decoded input / flag / candidate 明文写入 project_state artifact 或 report。
10. 不要修改 local_reverse_training_status.json。
11. 不要修改 training_materials/local_reverse/status_overlay.json。
12. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
13. 不要读取完整 solve_reports。
14. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不要提交 full solve_reports。
16. 不要把 task_packet.task 当执行权威。
17. 不要把 stale/missing/unknown artifact 当 current。
18. 不要把本轮变成训练状态同步或 runtime probe 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 修正 project_state/codex_execution_report.md。
4. 修正 project_state/pytest_result.txt。
5. 执行 JSON parse、py_compile、pytest、lint、git diff check。
6. 使用 git diff --name-status / git status --short 核对实际变更文件。
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
project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
```

必须确认以下文件不再出现在仓库根目录或 git diff 中：

```text
ida_evidence.json
sub_401014_key_init_analysis.json
sub_401120_analysis.json
xref_boundary_audit.json
```

必须运行并记录：

```text
git diff --name-status
git status --short
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
除 cpp2_883e67b9 当前 artifact 外的历史重型产物
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 tool_integration？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不生成/验证 candidate？
5. 根目录 JSON 工具输出是否仍已删除？
6. lint-report 是否重新运行且结果为 OK/PASS？
7. pytest_result.txt 中是否仍出现 lint-report FAILED？必须为否。
8. codex_execution_report.md 中是否仍出现 lint-report FAILED？必须为否。
9. pytest_result.txt 是否仍存在 FAILED 与 PASSED 并存矛盾？必须为否。
10. codex_report_summary.files_changed 是否与实际 diff 一致？
11. 是否仍保持 candidate_generated=false？
12. 是否仍保持 candidate_validation_attempted=false？
13. 是否仍保持 runtime_validation_attempted=false？
14. 是否没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty？
15. 是否没有修改 training_status/status_overlay？
16. 是否没有新增 artifact 或 artifact_index 噪声登记？
17. 是否运行 JSON parse 校验？
18. 是否运行 py_compile？
19. 是否运行相关 pytest？结果是多少？
20. 是否运行 lint-decision、lint-report、project_state status？
21. 是否运行 git diff --check、git status --short、git diff --name-status？
22. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Re-run lint-report and required checks

重新运行并记录：

```text
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
```

结果必须为 OK/PASS，不允许记录为 FAILED 后解释为 expected。

### Phase B — Fix report and pytest_result

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须绑定：

```text
decision_id=decision_20260608_cpp2_883e67b9_cleanup_lint_report_rework_v1
report_id=report_20260608_cpp2_883e67b9_cleanup_lint_report_rework_v1
round_id=round_20260608_cpp2_883e67b9_cleanup_lint_report_rework_v1
```

report 必须说明：

```text
1. 已重新运行 lint-report，结果 OK/PASS。
2. pytest_result 中不再出现 FAILED 与 PASSED 并存。
3. 根目录工具 dump 仍已删除。
4. files_changed 与实际 diff 一致。
5. 本轮未运行样本、未运行 IDA/Ghidra、未 runtime validation。
6. 本轮未生成 candidate。
```

### Phase C — Keep project_state stable

除非必要，不修改：

```text
project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
project_state/artifact_index.json
```

如果被修改，必须说明原因并重新计算 sha/size/provenance。

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py
.venv\Scripts\python -m py_compile reverse_agent/ida_scripts/xref_boundary_audit.py reverse_agent/ida_scripts/decompile_sub_401120.py reverse_agent/ida_scripts/decompile_sub_401014.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. lint-report 仍失败。
2. pytest_result.txt 中仍出现 FAILED 但 summary 写 PASSED。
3. codex_execution_report.md 中仍出现 FAILED 但 summary 写 SUCCESS/ACCEPTED。
4. report 的 files_changed 与实际 diff 不一致。
5. 根目录 JSON dump 仍在仓库中或 git diff 中。
6. 需要运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty 才能完成本轮。
7. 需要继续执行 IDA/Ghidra/static extraction。
8. 需要生成或验证 candidate。
9. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
10. lint-report/status 无法通过。
11. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 lint/report 清理完成且静态公式证据仍完整，可在下一轮单独生成 `reverse_solving` DECISION_PACKET，用于 candidate generation 和 runtime validation。
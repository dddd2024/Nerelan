```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_untracked_tool_outputs_cleanup_v1",
  "round_id": "round_20260608_cpp2_883e67b9_untracked_tool_outputs_cleanup_v1",
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

目标：清理上一轮错误提交的根目录工具输出 JSON，并修正 report 的实际变更文件列表。本轮只处理提交卫生和 project_state 报告一致性，不重新分析样本，不运行样本，不生成 candidate，不做 runtime validation，不继续 IDA/Ghidra 分析。

必须删除或撤回提交中的根目录工具 dump：

```text
ida_evidence.json
sub_401014_key_init_analysis.json
sub_401120_analysis.json
xref_boundary_audit.json
```

这些文件不应作为根目录产物提交。若确需长期保存，必须在后续单独设计受控 project_state artifact，并登记到 artifact_index；本轮默认删除，不做新 artifact 设计。

必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果删除这些文件不影响 `project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json` 内容，则不要无意义修改 artifact 或 artifact_index。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED，原因是：

```text
1. artifact 明文 redaction、pytest_result round、artifact_index.source_run 已基本修复。
2. 但实际提交包含根目录 JSON 工具输出：
   - ida_evidence.json
   - sub_401014_key_init_analysis.json
   - sub_401120_analysis.json
   - xref_boundary_audit.json
3. codex_execution_report.md 中 files_changed 只列出 project_state 4 个文件，没有如实列出上述根目录 JSON。
4. report 把这些根目录 JSON 说成 pre-existing untracked environment noise，但 GitHub compare 显示它们已经被提交。
```

当前允许保留的静态证据仍只应存在于已登记 project_state artifact：

```text
project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
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
3. 删除根目录 JSON 工具输出文件。
4. 修正 project_state/codex_execution_report.md。
5. 修正 project_state/pytest_result.txt。
6. 执行 JSON parse、py_compile、pytest、lint、git diff check。
7. 使用 git diff --name-status / git status --short 核对实际变更文件。
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

必须检查并删除或撤回：

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
5. 实际 git diff --name-status 文件列表是什么？
6. 根目录 JSON 工具输出是否已删除？
7. codex_report_summary.files_changed 是否与实际 diff 一致？
8. 是否仍保持 candidate_generated=false？
9. 是否仍保持 candidate_validation_attempted=false？
10. 是否仍保持 runtime_validation_attempted=false？
11. 是否没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty？
12. 是否没有修改 training_status/status_overlay？
13. 是否没有新增 artifact 或 artifact_index 噪声登记？
14. 是否运行 JSON parse 校验？
15. 是否运行 py_compile？
16. 是否运行相关 pytest？结果是多少？
17. 是否运行 lint-decision、lint-report、project_state status？
18. 是否运行 git diff --check、git status --short、git diff --name-status？
19. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Remove root tool dumps

删除或撤回以下文件：

```text
ida_evidence.json
sub_401014_key_init_analysis.json
sub_401120_analysis.json
xref_boundary_audit.json
```

不得把这些文件移动到其他目录作为本轮新 artifact。不得重新登记 artifact_index。

### Phase B — Fix report and pytest_result

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须绑定：

```text
decision_id=decision_20260608_cpp2_883e67b9_untracked_tool_outputs_cleanup_v1
report_id=report_20260608_cpp2_883e67b9_untracked_tool_outputs_cleanup_v1
round_id=round_20260608_cpp2_883e67b9_untracked_tool_outputs_cleanup_v1
```

report 必须说明：

```text
1. 已删除根目录工具 dump。
2. files_changed 与实际 diff 一致。
3. 本轮未运行样本、未运行 IDA/Ghidra、未 runtime validation。
4. 本轮未生成 candidate。
5. artifact_index 若未修改，说明原因；若修改，必须解释必要性。
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
1. 根目录 JSON 工具输出仍在 git diff 中。
2. files_changed 与实际 diff 不一致。
3. 需要运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty 才能完成本轮。
4. 需要继续执行 IDA/Ghidra/static extraction。
5. 需要生成或验证 candidate。
6. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
7. lint-report/status 无法通过。
8. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若清理完成且静态公式证据仍完整，可在下一轮单独生成 `reverse_solving` DECISION_PACKET，用于 candidate generation 和 runtime validation。
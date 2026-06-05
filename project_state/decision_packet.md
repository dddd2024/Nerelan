```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_reextract_scope_rework_v1",
  "round_id": "round_20260605_affine_reextract_scope_rework_v1",
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

上一轮 `decision_20260604_affine_main_input_flow_reextract_v1` 审计结论为 `REWORK_REQUIRED`。返工目标是修正上一轮 Codex 执行中的两个核心问题：

```text
1. scope 越界：新增了 reverse_agent/local_reverse_affine_main_input_flow_reextract.py，而上一轮 decision 只允许新增 project_state/local_reverse_affine_main_input_flow_reextract.json，并要求优先最小扩展 reverse_agent/local_reverse_targeted_static_reextract.py。
2. 测试记录不足：修改 Python 代码后没有记录 py_compile；没有记录 reextract bounded command 输出。
```

本轮目标：**把 affine main-input-flow reextract 能力迁移/合并到既有 `reverse_agent/local_reverse_targeted_static_reextract.py`，删除或停止使用上一轮新增的 affine 专用重复脚本，重新生成并登记 reextract artifact，补齐测试和报告记录。**

目标样本：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
```

本轮只做 **工程返工 + 静态 JSON 处理**。不得运行样本，不得运行 solver，不得生成 candidate 或 flag，不得 runtime probe，不得重新运行 IDA。

必须完成：

```text
1. 读取 project_state/task_packet.json、current_state.json、artifact_index.json、negative_results.json、codex_execution_report.md、decision_packet.md、pytest_result.txt。
2. 确认 task_packet.task 只是 advisory，本 decision_packet 是本轮唯一执行权威。
3. 检查 reverse_agent/local_reverse_affine_main_input_flow_reextract.py 与 reverse_agent/local_reverse_targeted_static_reextract.py。
4. 将上一轮 affine main-input-flow reextract 逻辑迁移/合并进 reverse_agent/local_reverse_targeted_static_reextract.py。
5. 删除 reverse_agent/local_reverse_affine_main_input_flow_reextract.py，或至少确保该专用重复入口不再作为长期入口存在；优先删除。
6. 保持旧 sha_256/CPP2 targeted static reextract 行为兼容。
7. 通过显式 CLI 参数支持 affine_8cfebe03，例如 --sample-id、--summary、--evidence、--mode affine-main-input-flow、--out。
8. 使用合并后的通用脚本重新生成 project_state/local_reverse_affine_main_input_flow_reextract.json。
9. 更新 artifact_index.json，把 local_reverse_affine_main_input_flow_reextract 登记为 current，source_run=round_20260605_affine_reextract_scope_rework_v1。
10. 更新 codex_execution_report.md 和 pytest_result.txt。
11. pytest_result.txt 必须记录 py_compile、required tests、bounded command 输出和 exit code。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍包含旧 samplereverse/local_reverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮可用但需返工的产物：

```text
project_state/local_reverse_affine_main_input_flow_reextract.json
  sample_id: affine_8cfebe03
  analysis_mode: targeted_static_reextract_main_input_flow
  executed_sample: false
  input_api: scanf
  format_string: %s
  buffer_candidates: [ebp+Str] (local stack buffer)
  candidate_transform_sites: []
  candidate_compare_sites: _strncmp/__GLOBAL_HEAP_SELECTED marked as CRT/heap noise
  blocker: MISSING_MAIN_0_PSEUDOCODE
  recommended_next_action: targeted_ida_decompile_specific_function
```

上一轮主要问题：

```text
reverse_agent/local_reverse_affine_main_input_flow_reextract.py was added outside Implementation Scope.
reverse_agent/local_reverse_targeted_static_reextract.py was not minimally extended as requested.
pytest_result.txt did not record python -m py_compile for the Python change.
pytest_result.txt did not record bounded command execution for the reextract script.
```

当前 affine IDA evidence 仍是本轮输入证据：

```text
project_state/local_reverse_affine_ida_summary.json
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
```

artifact_index 中应保持以下 current 证据不被覆盖或删除：

```text
local_reverse_affine_ida_summary
local_reverse_ida_evidence_affine_8cfebe03
```

已有工具能力：

```text
reverse_agent/local_reverse_targeted_static_reextract.py exists and must be reused/extended.
reverse_agent/tool_runners.py and reverse_agent/ida_scripts/collect_evidence.py already exist; do not create duplicate IDA/Ghidra runner.
Detailed affine IDA evidence JSON is already available; no IDA rerun is allowed this round.
```

`negative_results.json` 仍禁止 old sample_solver blind search、only increase beam/budget、commit full solve_reports、重复旧 runtime/probe 失败方向。本轮不得进入这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不重新运行 IDA。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA runner 或 Ghidra runner。
11. 不新建 affine 专用 solver。
12. 不把 affine 单题结论写入长期 skill。
13. 不保留 affine 专用重复 reextract 脚本作为主入口。
14. 不回到 old sample_solver blind search。
15. 不扩大 beam/budget/bruteforce。
16. 不把 CRT/debug heap 函数表述为业务验证函数。
17. 不把 IDA 静态证据等同于 runtime validation。
18. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
19. 不把 _strncmp/__GLOBAL_HEAP_SELECTED 当作业务 final compare。
```

允许：

```text
1. 读取当前 affine IDA summary 和 bounded detailed evidence JSON。
2. 修改 reverse_agent/local_reverse_targeted_static_reextract.py，做最小兼容扩展。
3. 删除上一轮新增的 reverse_agent/local_reverse_affine_main_input_flow_reextract.py。
4. 重新生成 project_state/local_reverse_affine_main_input_flow_reextract.json。
5. 修改或新增与 targeted reextract 直接相关的轻量测试。
6. 更新 artifact_index/codex_execution_report/pytest_result。
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
project_state/local_reverse_affine_ida_summary.json
project_state/local_reverse_affine_main_input_flow_reextract.json
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
reverse_agent/local_reverse_affine_main_input_flow_reextract.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

必要时检查：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
tests/test_project_state.py
tests/test_local_reverse_targeted_static_reextract.py
tests/test_local_reverse_inventory.py
tests/test_local_reverse_training_status.py
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
3. 是否确认目标样本是 affine_8cfebe03。
4. 是否确认 sample_id、relative_path、sha256、size_bytes、executed_sample=false 未被错误修改。
5. 是否确认 affine IDA summary 和 detailed evidence 在 artifact_index.latest_artifacts_v2 中 freshness=current。
6. 是否删除或迁移 reverse_agent/local_reverse_affine_main_input_flow_reextract.py。
7. 是否把 affine main-input-flow reextract 能力合并进 reverse_agent/local_reverse_targeted_static_reextract.py。
8. 是否保持旧 sha_256/CPP2 行为兼容。
9. 是否没有新建重复 parser/runner。
10. 是否没有运行 affine.exe。
11. 是否没有运行 solver、runtime probe、debugger、emulator。
12. 是否没有重新运行 IDA。
13. 是否没有上传原始样本。
14. 是否没有提交 full solve_reports。
15. 是否没有修改 .codex-skills。
16. 是否重新生成 project_state/local_reverse_affine_main_input_flow_reextract.json。
17. 是否将该 artifact 登记到 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_reextract_scope_rework_v1。
18. 是否明确区分 CRT/debug heap noise 与业务验证逻辑。
19. 是否没有把 _strncmp/__GLOBAL_HEAP_SELECTED 误判为业务 final compare。
20. 是否更新 codex_execution_report.md 和 pytest_result.txt。
21. pytest_result.txt 是否记录真实测试命令、bounded command、py_compile 且全部 Exit code 0。
22. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_reextract_scope_rework_v1。
```

---

## 6. Implementation Scope

允许删除：

```text
reverse_agent/local_reverse_affine_main_input_flow_reextract.py
```

允许修改：

```text
reverse_agent/local_reverse_targeted_static_reextract.py
project_state/local_reverse_affine_main_input_flow_reextract.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如需测试最小扩展，允许修改或新增与该脚本直接相关的轻量测试，例如：

```text
tests/test_local_reverse_targeted_static_reextract.py
```

实现约束：

```text
1. 优先在 reverse_agent/local_reverse_targeted_static_reextract.py 添加显式参数：--sample-id、--summary、--evidence、--mode、--out。
2. 新增 mode 值建议为 affine-main-input-flow。
3. 保持旧 sha_256/CPP2 行为兼容，不破坏现有 CLI 默认路径。
4. 不复制 IDA runner 逻辑。
5. 不新增 Ghidra runner。
6. 不新增 solver。
7. 不读取或提交原始 affine.exe。
8. 输出必须是结构化 JSON，便于下一轮审计和 solver 选择。
9. 如果因兼容性原因无法删除 affine 专用脚本，必须报告 BLOCKED，不得静默保留。
```

建议输出结构保持兼容：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "relative_path": "逆向课程2024春补考03/affine.exe",
  "analysis_mode": "targeted_static_reextract_main_input_flow",
  "executed_sample": false,
  "source_summary": "project_state/local_reverse_affine_ida_summary.json",
  "source_evidence": "solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json",
  "focus": {
    "function": "_main_0",
    "input_prompt_site": "0x401054",
    "scanf_site": "0x401065"
  },
  "input_flow": {
    "input_api": "scanf|unknown",
    "format_string": "%s|unknown",
    "buffer_candidates": [],
    "stack_variables": [],
    "post_scanf_reads": [],
    "post_scanf_writes": [],
    "calls_after_scanf": []
  },
  "candidate_transform_sites": [],
  "candidate_compare_sites": [],
  "noise_or_low_priority_sites": [],
  "confidence": "low|medium|high",
  "blockers": [],
  "recommended_next_action": "affine_constraint_recovery|targeted_ida_decompile_specific_function|blocked"
}
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_targeted_static_reextract.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

必须记录一次 bounded command，并确保 Exit code 0，例如：

```bash
python -m reverse_agent.local_reverse_targeted_static_reextract --sample-id affine_8cfebe03 --mode affine-main-input-flow --summary project_state/local_reverse_affine_ida_summary.json --evidence solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json --out project_state/local_reverse_affine_main_input_flow_reextract.json
```

如果新增或修改 targeted reextract 测试，必须运行：

```bash
python -m pytest -q tests/test_local_reverse_targeted_static_reextract.py
```

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPTED`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_ida_summary.json 缺失或 JSON 无法解析。
2. solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json 缺失或 JSON 无法解析。
3. artifact_index 中 affine summary/evidence 不是 freshness=current。
4. 迁移 affine reextract 逻辑会破坏旧 sha_256/CPP2 行为。
5. 需要运行 affine.exe 才能完成。
6. 需要 solver、runtime probe、debugger、emulator 才能完成。
7. 需要重新运行 IDA 或上传原始样本才能完成。
8. 需要提交 full solve_reports 才能完成。
9. artifact_index 更新会覆盖或删除既有 current local_reverse 证据。
10. 无法删除或迁移 reverse_agent/local_reverse_affine_main_input_flow_reextract.py。
```

完成条件：

```text
1. affine reextract 能力已合并进 reverse_agent/local_reverse_targeted_static_reextract.py。
2. reverse_agent/local_reverse_affine_main_input_flow_reextract.py 已删除或明确不再存在。
3. affine main input flow reextract artifact 已由通用 targeted reextract 脚本重新生成。
4. artifact 内容聚焦 _main_0 / scanf 后数据流，不混入 CRT/debug heap 误判。
5. artifact 登记进 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_reextract_scope_rework_v1。
6. report/pytest 与 decision_20260605_affine_reextract_scope_rework_v1 对齐。
7. required tests、py_compile、bounded command 全部记录且 Exit code 0。
8. 未运行样本、solver、runtime probe、debugger、emulator。
9. 未上传原始样本，未提交 full solve_reports。
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_main_input_flow_reextract_v1",
  "round_id": "round_20260604_affine_main_input_flow_reextract_v1",
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

上一轮 `decision_20260604_affine_detailed_evidence_consistency_rework_v1` 已被审计为 `ACCEPTED`。当前 affine 相关 IDA summary 和 detailed evidence 已是可审计 current artifact。

本轮目标：**对 `affine_8cfebe03` 做 `_main_0` / scanf 后输入数据流的 targeted static re-extract，提取输入缓冲区、输入长度、scanf 后局部变量流、候选变换逻辑和最终比较点线索。**

目标样本：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
```

本轮只做 **静态重提取**。不得运行样本，不得运行 solver，不得生成 candidate 或 flag，不得 runtime probe。

必须完成：

```text
1. 读取 project_state/local_reverse_affine_ida_summary.json。
2. 读取 solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json。
3. 确认 artifact_index 中 local_reverse_affine_ida_summary 与 local_reverse_ida_evidence_affine_8cfebe03 均为 freshness=current。
4. 复用已有 static/IDA evidence parsing 能力，优先最小扩展 reverse_agent/local_reverse_targeted_static_reextract.py。
5. 不新建重复 parser/runner；如果现有脚本只支持 sha_256/CPP2，则做最小兼容扩展以支持 affine_8cfebe03 的显式 sample_id / evidence path / output path。
6. 聚焦 _main_0 中 0x401054 puts 与 0x401065 scanf 附近及之后的数据流。
7. 提取并结构化记录：
   - scanf format / input buffer / stack variable names
   - `_main_0` 的 decompiler snippet 或 bounded disassembly context
   - scanf 后对输入缓冲区的 reads/writes/calls
   - 可能的 length checks / character range checks
   - 输入 buffer 到候选 transform/comparison call 的数据流
   - candidate transform sites
   - final compare / success / failure branch candidates
   - unresolved gaps and confidence
8. 生成 project_state/local_reverse_affine_main_input_flow_reextract.json。
9. 更新 artifact_index.json，把新 artifact 登记为 current。
10. 更新 codex_execution_report.md 和 pytest_result.txt。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory 状态，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前已接受证据：

```text
project_state/local_reverse_affine_ida_summary.json:
  sample_id: affine_8cfebe03
  relative_path: 逆向课程2024春补考03/affine.exe
  sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
  analysis_mode: ida_static_export
  executed_sample: false
  ida_status: success
  hexrays_available: true
  validation_function_candidates: []
  recommended_next_action: targeted_static_reextract_main_input_flow
  recommended_next_focus: _main_0 scanf/post-input data flow near 0x401054 and 0x401065
```

`artifact_index.latest_artifacts` 当前包含：

```text
local_reverse_affine_ida_summary = project_state\\local_reverse_affine_ida_summary.json
local_reverse_ida_evidence_affine_8cfebe03 = solve_reports\\tool_artifacts\\local_reverse_affine_ida_static_export_v1\\affine_8cfebe03\\affine_ida_evidence.json
```

`artifact_index.latest_artifacts_v2` 当前包含：

```text
local_reverse_affine_ida_summary:
  freshness: current
  source_run: round_20260604_affine_detailed_evidence_consistency_rework_v1

local_reverse_ida_evidence_affine_8cfebe03:
  freshness: current
  source_run: round_20260604_affine_detailed_evidence_consistency_rework_v1
  sample_id: affine_8cfebe03
```

关键静态线索：

```text
0x401054: _main_0 calls _puts, ref_strings: please input a string:
0x401065: _main_0 calls _scanf, ref_strings: please input a string: | %s
compare_sites currently include _strncmp with __GLOBAL_HEAP_SELECTED, which is CRT/heap-related and not business compare.
validation_function_candidates is intentionally empty.
noise_or_low_priority_functions includes CRT/debug heap functions such as sub_407A90, __CrtDbgReport, __heap_alloc_dbg.
solver_hints is downgraded to static_compare_api_context_only and console_input_flow_candidate.
```

Existing tool capability:

```text
reverse_agent/local_reverse_targeted_static_reextract.py exists, but current implementation is oriented to old sha_256/CPP2 unresolved targets and contains hard-coded expected sample ids.
reverse_agent/tool_runners.py and reverse_agent/ida_scripts/collect_evidence.py already exist; do not create duplicate IDA runner.
Detailed affine IDA evidence JSON is already committed and current; no IDA rerun is required for this round.
```

`negative_results.json` still forbids old sample_solver blind search, only increasing beam/budget, committing full solve_reports, and repeating old runtime/probe failed directions. This round must not enter any of those directions.

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不重新运行 IDA，除非现有 artifact 损坏且报告 BLOCKED；默认只解析已提交 evidence JSON。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA runner 或 Ghidra runner。
11. 不新建 affine 专用硬编码 solver。
12. 不把 affine 单题结论写入长期 skill。
13. 不回到 old sample_solver blind search。
14. 不扩大 beam/budget/bruteforce。
15. 不把 CRT/debug heap 函数表述为业务验证函数。
16. 不把 IDA 静态证据等同于 runtime validation。
17. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
18. 不把当前 _strncmp/__GLOBAL_HEAP_SELECTED 当作业务 final compare。
```

允许：

```text
1. 读取当前 affine IDA summary 和 bounded detailed evidence JSON。
2. 最小修改 reverse_agent/local_reverse_targeted_static_reextract.py，使其支持显式 sample_id/evidence path/output path 或 affine main-input-flow 模式。
3. 新增小型 project_state JSON 结果。
4. 修改 tests 中与该最小扩展直接相关的测试。
5. 更新 artifact_index/codex_execution_report/pytest_result。
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
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
reverse_agent/local_reverse_targeted_static_reextract.py
```

必要时检查：

```text
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
tests/test_project_state.py
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
6. 是否复用已有 targeted static reextract / IDA evidence parsing 能力。
7. 如果修改 local_reverse_targeted_static_reextract.py，是否只是最小兼容扩展，而不是新建重复 parser/runner。
8. 是否没有运行 affine.exe。
9. 是否没有运行 solver、runtime probe、debugger、emulator。
10. 是否没有重新运行 IDA。
11. 是否没有上传原始样本。
12. 是否没有提交 full solve_reports。
13. 是否没有修改 .codex-skills。
14. 是否提取了 _main_0 / scanf 后输入数据流证据。
15. 是否明确区分 CRT/debug heap noise 与业务验证逻辑。
16. 是否没有把 _strncmp/__GLOBAL_HEAP_SELECTED 误判为业务 final compare。
17. 是否生成 project_state/local_reverse_affine_main_input_flow_reextract.json。
18. 是否将该 artifact 登记到 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260604_affine_main_input_flow_reextract_v1。
19. 是否更新 codex_execution_report.md 和 pytest_result.txt。
20. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
21. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_main_input_flow_reextract_v1。
```

---

## 6. Implementation Scope

允许新增：

```text
project_state/local_reverse_affine_main_input_flow_reextract.json
```

允许修改：

```text
reverse_agent/local_reverse_targeted_static_reextract.py
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
1. 优先添加显式参数，例如 --sample-id、--raw-evidence、--summary、--mode affine-main-input-flow、--out。
2. 保持旧 sha_256/CPP2 行为兼容，不破坏现有 CLI 默认路径。
3. 不复制 IDA runner 逻辑。
4. 不新增 Ghidra runner。
5. 不新增 solver。
6. 不读取或提交原始 affine.exe。
7. 输出必须是结构化 JSON，便于下一轮审计和 solver 选择。
```

建议输出结构：

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
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果修改任何 Python 代码，必须额外运行：

```bash
python -m py_compile reverse_agent/local_reverse_targeted_static_reextract.py
```

如果新增或修改 targeted reextract 测试，必须运行：

```bash
python -m pytest -q tests/test_local_reverse_targeted_static_reextract.py
```

如果没有新增专门测试，必须在 report 中说明原因，并至少记录对脚本的 bounded command 运行输出。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPTED`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_ida_summary.json 缺失或 JSON 无法解析。
2. solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json 缺失或 JSON 无法解析。
3. artifact_index 中 affine summary/evidence 不是 freshness=current。
4. evidence 中找不到 _main_0、0x401054、0x401065 或 scanf/puts 相关上下文，且无法通过已有 evidence 做有界提取。
5. 完成本轮需要运行 affine.exe。
6. 完成本轮需要 solver、runtime probe、debugger、emulator。
7. 完成本轮需要重新运行 IDA 或上传原始样本。
8. 完成本轮需要提交 full solve_reports。
9. 对 local_reverse_targeted_static_reextract.py 的修改会破坏旧 sha_256/CPP2 行为。
10. artifact_index 更新会覆盖或删除既有 current local_reverse 证据。
```

完成条件：

```text
1. affine main input flow reextract artifact 已生成。
2. artifact 内容聚焦 _main_0 / scanf 后数据流，不混入 CRT/debug heap 误判。
3. artifact 登记进 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current。
4. report/pytest 与 decision_20260604_affine_main_input_flow_reextract_v1 对齐。
5. required tests 全部记录且 Exit code 0。
6. 未运行样本、solver、runtime probe、debugger、emulator。
7. 未上传原始样本，未提交 full solve_reports。
```

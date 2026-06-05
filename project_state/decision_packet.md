```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_affine_main0_targeted_ida_decompile_v1",
  "round_id": "round_20260605_affine_main0_targeted_ida_decompile_v1",
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

上一轮 `decision_20260605_affine_reextract_test_record_rework_v1` 已被审计为 `ACCEPTED`。当前技术 blocker 是 `project_state/local_reverse_affine_main_input_flow_reextract.json` 中记录的：

```text
MISSING_MAIN_0_PSEUDOCODE: _main_0 decompiler snippet not in raw evidence; core affine transform logic cannot be confirmed without targeted IDA decompilation of _main_0
```

本轮目标：**使用现有 IDA/Hex-Rays 工具链，对 `affine_8cfebe03` 的 `_main_0` 做有界 targeted decompilation/export，补齐 `_main_0` 伪代码或 bounded disassembly evidence，并生成可审计 JSON。**

目标样本：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
```

本轮只允许 **IDA/Hex-Rays 静态导出**。不得运行样本，不得运行 solver，不得生成 candidate 或 flag，不得 runtime probe，不得 debugger/emulator。

必须完成：

```text
1. 读取 project_state/task_packet.json、current_state.json、artifact_index.json、negative_results.json、codex_execution_report.md、decision_packet.md、pytest_result.txt。
2. 确认 task_packet.task 只是 advisory，本 decision_packet 是本轮唯一执行权威。
3. 确认 artifact_index 中 local_reverse_affine_ida_summary、local_reverse_ida_evidence_affine_8cfebe03、local_reverse_affine_main_input_flow_reextract 均为 freshness=current。
4. 检查已有 IDA 能力：reverse_agent/tool_runners.py 与 reverse_agent/ida_scripts/collect_evidence.py。
5. 不新建重复 IDA runner；优先最小扩展 reverse_agent/ida_scripts/collect_evidence.py，使其支持 forced function/eaddr decompile，例如通过 env 或 argv 指定 _main_0 / 0x401000-0x401100。
6. 使用现有 IDA runner/IDAPython/Hex-Rays 能力，对 affine.exe 的 _main_0 做 targeted static export。
7. 输出必须结构化记录：
   - sample_id、relative_path、sha256、executed_sample=false
   - ida_status、hexrays_available、target_function、target_ea/range
   - _main_0 pseudocode（如可用）
   - _main_0 bounded disassembly context（即使 pseudocode 不可用也要提供）
   - scanf/puts/input buffer evidence
   - post-scanf reads/writes/calls within _main_0
   - candidate transform sites
   - candidate compare/success/failure branch sites
   - unresolved gaps and confidence
8. 生成 project_state/local_reverse_affine_main0_targeted_ida_decompile.json。
9. 更新 artifact_index.json，把新 artifact 登记到 latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_main0_targeted_ida_decompile_v1。
10. 更新 codex_execution_report.md 和 pytest_result.txt。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍包含旧 samplereverse/local_reverse advisory 信息，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮已接受状态：

```text
codex_execution_report.md:
  report_id: report_20260605_affine_reextract_test_record_rework_v1
  based_on_decision_id: decision_20260605_affine_reextract_test_record_rework_v1
  status: SUCCESS
  tests_ran: py_compile, pytest, lint-decision, lint-report, bounded command, git diff --check, git status --short

pytest_result.txt:
  status: PASSED
  Total Commands: 7
  Passed: 7
```

当前 affine 相关 artifact：

```text
local_reverse_affine_ida_summary:
  path: project_state/local_reverse_affine_ida_summary.json
  freshness: current
  source_run: round_20260604_affine_detailed_evidence_consistency_rework_v1

local_reverse_ida_evidence_affine_8cfebe03:
  path: solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
  freshness: current
  source_run: round_20260604_affine_detailed_evidence_consistency_rework_v1
  sample_id: affine_8cfebe03

local_reverse_affine_main_input_flow_reextract:
  path: project_state/local_reverse_affine_main_input_flow_reextract.json
  freshness: current
  source_run: round_20260605_affine_reextract_scope_rework_v1
  sample_id: affine_8cfebe03
```

关键 blocker：

```text
_main_0 pseudocode NOT available in raw IDA evidence.
collect_evidence.py scoring did not include _main_0 in top-6 decompiler snippets.
Input flow was extracted only from local_check_contexts and string_xrefs.
```

已有工具能力：

```text
reverse_agent/tool_runners.py:
  - 已有 run_ida_evidence(...) 和 _run_ida(...)。
  - _run_ida 使用 IDA -A、-L、-o、-S，并通过 REVERSE_AGENT_IDA_OUT 指定 JSON 输出。
  - 不需要新建重复 IDA runner。

reverse_agent/ida_scripts/collect_evidence.py:
  - 已有字符串、函数、compare_contexts、local_check_contexts、string_xrefs、validation_function_candidates、Hex-Rays snippets 导出能力。
  - 现有 _collect_decompiler_snippets(...) 只对 validation_function_candidates top candidates 做 decompile，limit 默认 6。
  - 本轮应最小扩展该脚本，支持 forced _main_0 decompile/export，而不是重写 IDA 能力。
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
5. 不上传 E:\reverse 原始样本。
6. 不复制 affine.exe 到仓库。
7. 不提交 full solve_reports 目录。
8. 不修改 .codex-skills。
9. 不新建重复 IDA runner 或 Ghidra runner。
10. 不新建 affine 专用 solver。
11. 不把 affine 单题结论写入长期 skill。
12. 不回到 old sample_solver blind search。
13. 不扩大 beam/budget/bruteforce。
14. 不把 CRT/debug heap 函数表述为业务验证函数。
15. 不把 IDA 静态证据等同于 runtime validation。
16. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
17. 不把 _strncmp/__GLOBAL_HEAP_SELECTED 当作业务 final compare。
18. 不删除或回退上一轮已接受的 affine reextract artifact。
19. 不重新引入 reverse_agent/local_reverse_affine_main_input_flow_reextract.py。
```

允许：

```text
1. 运行 IDA/Hex-Rays 静态分析，仅限 affine_8cfebe03 的 _main_0 targeted export。
2. 最小扩展 reverse_agent/ida_scripts/collect_evidence.py，使其支持 forced function/eaddr decompile/export。
3. 必要时最小扩展 tool_runners.py 传递 forced target env/args；不得复制 runner。
4. 生成 project_state/local_reverse_affine_main0_targeted_ida_decompile.json。
5. 更新 artifact_index/codex_execution_report/pytest_result。
6. 新增或修改与 forced IDA export 直接相关的轻量测试。
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
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_targeted_static_reextract.py
```

必要时检查：

```text
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
5. 是否确认 affine IDA summary、detailed evidence、main-input-flow reextract 在 artifact_index.latest_artifacts_v2 中 freshness=current。
6. 是否检查并复用已有 IDA runner / IDAPython script。
7. 是否没有新建重复 IDA/Ghidra runner。
8. 如果修改 collect_evidence.py，是否只是最小 forced decompile/export 扩展。
9. 是否只对 _main_0 / 0x401000-0x401100 做 targeted static export。
10. 是否没有运行 affine.exe。
11. 是否没有运行 solver、runtime probe、debugger、emulator。
12. 是否没有上传原始样本。
13. 是否没有提交 full solve_reports。
14. 是否没有修改 .codex-skills。
15. 是否生成 project_state/local_reverse_affine_main0_targeted_ida_decompile.json。
16. 是否将该 artifact 登记到 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_main0_targeted_ida_decompile_v1。
17. 是否明确区分 IDA static evidence 与 runtime validation。
18. 是否没有把 _strncmp/__GLOBAL_HEAP_SELECTED 误判为业务 final compare。
19. 是否更新 codex_execution_report.md 和 pytest_result.txt。
20. pytest_result.txt 是否记录真实测试命令、IDA command 或 BLOCKED 原因、Exit code。
21. codex_report_summary.based_on_decision_id 是否等于 decision_20260605_affine_main0_targeted_ida_decompile_v1。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/ida_scripts/collect_evidence.py
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时允许最小修改：

```text
reverse_agent/tool_runners.py
```

允许新增：

```text
project_state/local_reverse_affine_main0_targeted_ida_decompile.json
```

如需测试 forced export helper，允许新增或修改直接相关的轻量测试，例如：

```text
tests/test_ida_collect_evidence_forced_targets.py
```

实现约束：

```text
1. 优先在 reverse_agent/ida_scripts/collect_evidence.py 中添加 forced targets 机制，例如：
   - REVERSE_AGENT_IDA_FORCE_FUNCS=_main_0
   - REVERSE_AGENT_IDA_FORCE_EAS=0x401000
   - REVERSE_AGENT_IDA_FORCE_RANGE=0x401000:0x401100
   - 或等价 argv 参数。
2. forced export 应追加字段，不破坏旧字段：
   - forced_decompiler_snippets
   - forced_disassembly_contexts
   - forced_targets
   - forced_export_errors
3. 保持旧 collect_evidence.py 默认行为兼容；未设置 forced target 时，原输出字段和 top-candidate snippets 不应被破坏。
4. 不复制 IDA runner 逻辑。
5. 不新增 Ghidra runner。
6. 不新增 solver。
7. 不读取或提交原始 affine.exe。
8. 输出必须是结构化 JSON，便于下一轮 reextract/solver 选择。
9. 如果 IDA/Hex-Rays 不可用或本地样本不可用，必须报告 BLOCKED，不得伪造 artifact。
```

建议 `project_state/local_reverse_affine_main0_targeted_ida_decompile.json` 结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "relative_path": "逆向课程2024春补考03/affine.exe",
  "analysis_mode": "targeted_ida_decompile_main0",
  "executed_sample": false,
  "ida_static_only": true,
  "source_summary": "project_state/local_reverse_affine_ida_summary.json",
  "source_reextract": "project_state/local_reverse_affine_main_input_flow_reextract.json",
  "target": {
    "function": "_main_0",
    "ea": "0x401000",
    "range": "0x401000-0x401100"
  },
  "ida_status": "success|blocked|failed",
  "hexrays_available": true,
  "pseudocode_available": true,
  "pseudocode": "...",
  "bounded_disassembly_context": [],
  "input_flow_evidence": {},
  "post_scanf_flow_evidence": {},
  "candidate_transform_sites": [],
  "candidate_compare_sites": [],
  "success_failure_branch_candidates": [],
  "confidence": "low|medium|high",
  "blockers": [],
  "recommended_next_action": "rerun_main_input_reextract|affine_constraint_recovery|blocked"
}
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/ida_scripts/collect_evidence.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
```

如果修改 `reverse_agent/tool_runners.py`，必须额外运行：

```bash
python -m py_compile reverse_agent/tool_runners.py
```

如果新增或修改 forced IDA export 测试，必须运行：

```bash
python -m pytest -q tests/test_ida_collect_evidence_forced_targets.py
```

必须记录 IDA targeted export 命令及结果：

```text
- IDA command line or runner invocation
- Exit code
- output artifact path
- whether Hex-Rays pseudocode for _main_0 was produced
```

如果本地环境没有 IDA/Hex-Rays 或 affine.exe，必须：

```text
1. 不伪造成功。
2. codex_execution_report.md 写 BLOCKED。
3. pytest_result.txt 记录已运行的静态测试和明确 BLOCKED 原因。
4. 不更新 artifact_index 为 current 的新 targeted artifact。
```

所有 required non-IDA commands 必须 Exit code 0。IDA command 如果失败，报告必须是 BLOCKED 或 FAILED，不能写 SUCCESS/ACCEPTED。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_ida_summary.json 缺失或 JSON 无法解析。
2. project_state/local_reverse_affine_main_input_flow_reextract.json 缺失或 JSON 无法解析。
3. solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json 缺失或 JSON 无法解析。
4. artifact_index 中 affine summary/evidence/main-input-flow reextract 不是 freshness=current。
5. 本地 IDA/Hex-Rays 不可用。
6. 本地 affine.exe 不可用。
7. 完成本轮需要运行 affine.exe。
8. 完成本轮需要 solver、runtime probe、debugger、emulator。
9. 完成本轮需要上传原始样本。
10. 完成本轮需要提交 full solve_reports。
11. forced decompile 扩展会破坏 collect_evidence.py 旧默认行为。
12. 需要新建重复 IDA/Ghidra runner 才能完成。
```

完成条件：

```text
1. project_state/local_reverse_affine_main0_targeted_ida_decompile.json 已生成。
2. artifact 内容明确 executed_sample=false、ida_static_only=true。
3. artifact 包含 _main_0 pseudocode；如果 Hex-Rays 不可用，则包含 bounded disassembly context 和明确 blocker。
4. artifact 登记进 artifact_index.latest_artifacts 和 latest_artifacts_v2，freshness=current，source_run=round_20260605_affine_main0_targeted_ida_decompile_v1。
5. report/pytest 与 decision_20260605_affine_main0_targeted_ida_decompile_v1 对齐。
6. required tests、git diff --check、git status --short、IDA targeted command 全部记录。
7. 未运行样本、solver、runtime probe、debugger、emulator。
8. 未上传原始样本，未提交 full solve_reports。
```

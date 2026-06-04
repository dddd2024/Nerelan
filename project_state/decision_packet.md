```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_ida_static_export_v1",
  "round_id": "round_20260604_affine_ida_static_export_v1",
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

上一轮 `decision_20260604_affine_static_feature_index_repair_v1` 已完成 artifact 索引返工：

```text
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
```

两个 artifact 已进入 `artifact_index.latest_artifacts` 和 `artifact_index.latest_artifacts_v2`，且 `latest_artifacts_v2` 标记为 `freshness=current`。

当前 affine 静态特征 summary 给出的下一步是：

```text
recommended_next_action: run_ida_static_export
reason: Static strings reveal input/compare logic but no transform constants. IDA static export needed to locate the compare function and extract affine/shift parameters.
```

本轮目标：**复用已有 IDA 静态导出能力，对 `affine_8cfebe03` 做 IDA static export，提取函数、字符串引用、比较点、关键常量、伪代码/反汇编上下文，并登记为 current 工具证据。**

目标样本：

```text
sample_id: affine_8cfebe03
relative_path: 逆向课程2024春补考03/affine.exe
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
training_status: inventory_only
```

本轮只做 **IDA 静态证据导出**。不求解 flag，不生成 candidate，不运行样本，不运行 runtime probe。

必须完成：

```text
1. 读取 project_state/local_reverse_affine_static_feature_result.json。
2. 读取 project_state/local_reverse_affine_static_feature_summary.json。
3. 确认 artifact_index 中两个 affine static feature artifact 的 freshness=current。
4. 确认 affine_8cfebe03 仍是目标样本，且仍为 inventory_only。
5. 通过 LOCAL_REVERSE_ROOT + relative_path 定位本地样本。
6. 校验本地 affine.exe sha256 等于 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659。
7. 复用已有 IDA 接口，不新建重复 runner：
   - reverse_agent/tool_runners.py
   - reverse_agent/local_reverse_ida_summary.py
   - 现有 IDAPython 脚本/runner 配置
8. 运行 IDA 静态导出，采集：
   - file format / architecture / entry point
   - function list
   - imports
   - strings and xrefs
   - compare-related functions / callsites
   - references to `please input a string:`
   - references to `flag == 0 || flag == 1`
   - small numeric constants and byte constants near candidate compare/transform functions
   - available decompiler pseudocode, if Hex-Rays is available
   - bounded disassembly context if decompiler is unavailable
9. 生成 project_state/local_reverse_affine_ida_summary.json。
10. 如现有 runner 产生详细 evidence JSON，可生成 bounded tool artifact，并在 summary 中引用它。
11. 更新 artifact_index.json，将本轮 IDA summary/evidence 登记为 current。
12. 更新 codex_execution_report.md 和 pytest_result.txt。
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍保留旧 samplereverse 派生任务和 do_not_do 列表；它是 advisory，不是本轮执行权威。本轮以本 `project_state/decision_packet.md` 为准。

`artifact_index.json` 当前已登记：

```text
latest_artifacts.local_reverse_affine_static_feature_result = project_state\\local_reverse_affine_static_feature_result.json
latest_artifacts.local_reverse_affine_static_feature_summary = project_state\\local_reverse_affine_static_feature_summary.json
```

`latest_artifacts_v2` 当前已登记：

```text
local_reverse_affine_static_feature_result:
  freshness: current
  source_run: round_20260604_affine_static_feature_index_repair_v1
  path: project_state\\local_reverse_affine_static_feature_result.json

local_reverse_affine_static_feature_summary:
  freshness: current
  source_run: round_20260604_affine_static_feature_index_repair_v1
  path: project_state\\local_reverse_affine_static_feature_summary.json
```

`local_reverse_affine_static_feature_summary.json` 显示：

```text
analysis_mode: static_only
executed_sample: false
likely_category: strcmp_or_flag_check
confidence: medium
has_compare_strings: true
has_input_prompt: true
has_affine_constants: false
needs_ida_static_export: true
recommended_next_mainline: tool_integration
recommended_next_action: run_ida_static_export
forbidden_next_actions: runtime_probe, execute_sample, bruteforce, upload_binary
```

`current_state.json` 的 `local_reverse_training` 显示已有 IDA 能力：

```text
stage: ida_evidence_ready
ida_available: true
hexrays_available_any: true
latest_summary: project_state\\local_reverse_ida_summary.json
source_run: round_20260603_local_reverse_ida_path_rerun_v1
```

已有相关工具能力：

```text
reverse_agent/tool_runners.py: present, has IDA evidence runner and structured artifact conversion
reverse_agent/local_reverse_ida_summary.py: present, can run local_reverse IDA summary
reverse_agent/local_reverse_ida_guided_solver.py: present, but do not run solver this round
reverse_agent/local_reverse_forced_ida_extract.py: present, only use if local_reverse_ida_summary cannot target affine and the action remains static-only
reverse_agent/local_reverse_targeted_static_reextract.py: present, do not run this round unless IDA summary output format already calls it as static-only helper
Ghidra runner: missing, do not create one this round
```

`negative_results.json` still forbids returning to old blind search, only increasing beam/budget, committing full `solve_reports`, and repeating old failed runtime/probe paths. This round is a fresh static tool-integration step for affine and must not enter those failed directions.

Known limitation from previous audit: `artifact_index.generated_at` may still be stale. This should be repaired if project_state build can do it safely, but do not let this become a broader project_state refactor.

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不运行 IDA 动态调试；只允许 IDA 静态分析/静态导出。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA runner 或 Ghidra runner。
11. 不新建 affine 专用硬编码 solver。
12. 不把 affine 单题结论写入长期 skill。
13. 不回到 old sample_solver blind search。
14. 不扩大 beam/budget/bruteforce。
15. 不把 stale/missing artifact 当作 current evidence。
16. 不把 IDA 静态证据等同于 runtime validation。
17. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
```

允许：

```text
1. 使用 LOCAL_REVERSE_ROOT 读取本地 affine.exe 的 bytes 用于 sha256 校验和 IDA 静态导出。
2. 复用现有 IDA runner / IDAPython 脚本 / tool_runners.py。
3. 生成 project_state 下的小型 JSON summary。
4. 生成 bounded tool artifact，但必须登记到 artifact_index，不得提交 full solve_reports。
5. 如果 IDA executable 未配置或不可用，停止并报告 BLOCKED。
6. 如果 Hex-Rays 不可用，允许退化到函数列表、XREF、字符串、反汇编上下文，不得失败扩大范围。
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
project_state/local_reverse_affine_static_feature_result.json
project_state/local_reverse_affine_static_feature_summary.json
project_state/local_reverse_inventory.json
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
```

必要时检查：

```text
reverse_agent/local_reverse_inventory.py
reverse_agent/local_reverse_corpus.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_targeted_static_reextract.py
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
3. 是否确认 affine_8cfebe03 是目标样本。
4. 是否确认 affine_8cfebe03 仍为 inventory_only，未误标 solved。
5. 是否确认两个 affine static feature artifact 在 artifact_index.latest_artifacts_v2 中 freshness=current。
6. 是否通过 LOCAL_REVERSE_ROOT 定位本地样本。
7. 是否校验本地样本 sha256 匹配。
8. 是否复用已有 IDA runner / local_reverse_ida_summary.py / tool_runners.py。
9. 是否没有新建重复 IDA/Ghidra runner。
10. 是否只运行 IDA 静态导出，没有执行样本。
11. 是否没有运行 solver、runtime probe、debugger、emulator。
12. 是否提取函数、字符串 XREF、compare/callsite/import/constant/decompiler 或 disassembly evidence。
13. 是否生成 project_state/local_reverse_affine_ida_summary.json。
14. 是否将 IDA summary/evidence 登记到 artifact_index.latest_artifacts 和 latest_artifacts_v2。
15. latest_artifacts_v2 是否包含 freshness=current、source_run、本轮 path、sha256、size_bytes、modified_at。
16. 是否没有上传原始样本。
17. 是否没有提交 full solve_reports。
18. 是否没有修改 .codex-skills。
19. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
20. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_ida_static_export_v1。
```

---

## 6. Implementation Scope

允许新增：

```text
project_state/local_reverse_affine_ida_summary.json
```

如果现有 runner 需要详细 evidence artifact，允许新增 bounded artifact，例如：

```text
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
```

但不得提交 full `solve_reports`。如只登记 path/provenance 而不提交详细 artifact，也必须在 report 说明原因。

允许修改：

```text
project_state/artifact_index.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有在现有 runner 无法选择单个 local_reverse sample 时，才允许做最小兼容修复；允许修改范围：

```text
reverse_agent/local_reverse_ida_summary.py
reverse_agent/tool_runners.py
tests/test_project_state.py
```

最小兼容修复只能做：

```text
1. 支持通过 sample_id 或 relative_path 选择 affine_8cfebe03。
2. 保持已有三样本 IDA summary 行为不破坏。
3. 不复制 IDA invocation 逻辑。
4. 不添加 Ghidra runner。
5. 不添加 solver。
```

建议 `local_reverse_affine_ida_summary.json` 结构：

```json
{
  "schema_version": 1,
  "sample_id": "affine_8cfebe03",
  "relative_path": "逆向课程2024春补考03/affine.exe",
  "sha256": "8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659",
  "analysis_mode": "ida_static_export",
  "executed_sample": false,
  "ida_status": "success|blocked|partial",
  "hexrays_available": true,
  "functions": [],
  "imports": [],
  "strings": [],
  "xrefs": [],
  "compare_sites": [],
  "candidate_transform_sites": [],
  "interesting_constants": [],
  "evidence_artifacts": [],
  "recommended_next_action": "targeted_static_reextract|constraint_recovery|blocked",
  "limitations": []
}
```

`artifact_index.latest_artifacts_v2` 建议新增：

```text
local_reverse_affine_ida_summary:
  kind: local_reverse_affine_ida_summary
  path: project_state\\local_reverse_affine_ida_summary.json
  freshness: current
  source_run: round_20260604_affine_ida_static_export_v1
  sha256: <computed>
  size_bytes: <computed>
  modified_at: <timestamp>
  sample_id: affine_8cfebe03
```

若生成详细 evidence artifact，也登记：

```text
local_reverse_ida_evidence_affine_8cfebe03:
  kind: local_reverse_ida_evidence_affine_8cfebe03
  path: <bounded evidence path>
  freshness: current
  source_run: round_20260604_affine_ida_static_export_v1
  sample_id: affine_8cfebe03
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
python -m py_compile <modified_python_file>
```

如果修改 `local_reverse_ida_summary.py` 或 `tool_runners.py`，必须额外运行相关测试；若没有专门测试，至少运行：

```bash
python -m pytest -q tests/test_project_state.py tests/test_local_reverse_inventory.py tests/test_local_reverse_training_status.py
```

如果 IDA 不可用或 LOCAL_REVERSE_ROOT 未配置导致本轮 BLOCKED，仍必须运行可运行的 lint/test，并在 `pytest_result.txt` 记录实际结果。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPT`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. LOCAL_REVERSE_ROOT 未设置。
2. affine.exe 本地文件不存在。
3. affine.exe sha256 与 inventory/summary 不一致。
4. IDA executable 未配置或不可用。
5. 现有 IDA runner 无法静态导出，且修复会变成新建重复 runner。
6. 完成本轮需要执行 affine.exe。
7. 完成本轮需要 debugger/runtime probe/emulator。
8. 完成本轮需要运行 solver 或生成 candidate/flag。
9. 完成本轮需要上传原始样本。
10. 完成本轮需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
11. IDA 输出会泄露本地绝对路径且无法清洗。
12. artifact_index 更新会覆盖或删除既有 current local_reverse 证据。
```

完成条件：

```text
1. affine IDA 静态导出完成，或明确 BLOCKED 原因。
2. 样本未执行。
3. 未运行 solver/debugger/runtime probe。
4. 未上传原始样本。
5. IDA summary/evidence 已生成并登记到 artifact_index，或 BLOCKED 时说明未生成原因。
6. artifact freshness/provenance 可审计。
7. report/pytest 与 decision_20260604_affine_ida_static_export_v1 对齐。
8. required tests 全部记录。
```

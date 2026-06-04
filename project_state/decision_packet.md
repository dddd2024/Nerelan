```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_detailed_evidence_consistency_rework_v1",
  "round_id": "round_20260604_affine_detailed_evidence_consistency_rework_v1",
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

上一轮 `decision_20260604_affine_ida_static_export_rework_v1` 已完成部分返工：

```text
1. relative_path 已修正为 逆向课程2024春补考03/affine.exe。
2. CRT/debug heap 函数已从 validation_function_candidates 降级到 noise_or_low_priority_functions。
3. 下一步建议已收敛到 _main_0 / scanf 后数据流。
```

但审计结论仍为 `REWORK_REQUIRED`。本轮目标：**只修复 detailed evidence artifact 的提交/登记一致性，并降级仍偏强的 solver_hints。**

必须修复两个硬问题：

```text
1. codex_execution_report.md、artifact_index.json、local_reverse_affine_ida_summary.json 仍引用：
   solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
   但该文件未提交到 GitHub，读取返回 404。

2. artifact_index.latest_artifacts_v2 将 local_reverse_ida_evidence_affine_8cfebe03 标记为 freshness=current，但该 path 对应文件不存在于仓库，不能作为 current evidence。
```

同时修复一个非阻塞但必须收敛的解释问题：

```text
summary 中 solver_hints 仍包含 direct_strcmp / compare API context recovered。由于当前 compare_sites 仍是 _strncmp + __GLOBAL_HEAP_SELECTED 这类 CRT/heap context，该 hint 应降级为 static_compare_api_context_only 或 business_compare_not_confirmed，不能暗示业务比较已恢复。
```

本轮不是重新 IDA 导出，不是求解 affine，不生成 candidate，不输出 flag。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory 状态，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前已确认的有效证据：

```text
project_state/local_reverse_affine_ida_summary.json:
  sample_id: affine_8cfebe03
  relative_path: 逆向课程2024春补考03/affine.exe
  sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
  size_bytes: 196688
  analysis_mode: ida_static_export
  executed_sample: false
  ida_status: success
  hexrays_available: true
  validation_function_candidates: []
  recommended_next_action: targeted_static_reextract_main_input_flow
  recommended_next_focus: _main_0 scanf/post-input data flow near 0x401054 and 0x401065
```

当前仍不一致的证据：

```text
codex_execution_report.md.generated_artifacts contains:
  solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json

artifact_index.latest_artifacts_v2 contains:
  local_reverse_ida_evidence_affine_8cfebe03:
    path: solve_reports\\tool_artifacts\\local_reverse_affine_ida_static_export_v1\\affine_8cfebe03\\affine_ida_evidence.json
    freshness: current

local_reverse_affine_ida_summary.json.evidence_artifacts contains:
  solve_reports\\tool_artifacts\\local_reverse_affine_ida_static_export_v1\\affine_8cfebe03\\affine_ida_evidence.json
```

审计已确认：该 path 在 GitHub 中读取返回 404；上一轮 commit diff 也没有新增 `solve_reports/.../affine_ida_evidence.json`。

当前 `artifact_index.latest_artifacts` 旧字段也没有登记 `local_reverse_ida_evidence_affine_8cfebe03`。如果选择提交 detailed evidence，则必须补旧字段；如果不提交 detailed evidence，则必须彻底移除 v2 和 report/summary 中的引用。

`negative_results.json` 仍禁止 old sample_solver blind search、只扩大 beam/budget、提交 full solve_reports、重复旧 runtime/probe 失败方向。本轮不涉及这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不重新运行 IDA，除非仅为确认本地 detailed evidence 文件是否存在且不扩大范围。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA runner 或 Ghidra runner。
11. 不新建 affine 专用硬编码 solver。
12. 不把 affine 单题结论写入长期 skill。
13. 不回到 old sample_solver blind search。
14. 不扩大 beam/budget/bruteforce。
15. 不把不存在于 GitHub 的 artifact 标记为 freshness=current。
16. 不把 IDA 静态证据等同于 runtime validation。
17. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
```

允许：

```text
1. 编辑 project_state/local_reverse_affine_ida_summary.json。
2. 编辑 project_state/artifact_index.json。
3. 编辑 project_state/codex_execution_report.md。
4. 编辑 project_state/pytest_result.txt。
5. 二选一处理 detailed evidence：提交单个 bounded JSON 并登记，或从所有 current/report/summary 引用中移除。
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
```

可有界检查是否存在：

```text
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
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
4. 是否确认 local_reverse_affine_ida_summary.json 的 relative_path 已是 逆向课程2024春补考03/affine.exe。
5. 是否确认 sample_id、sha256、size_bytes、executed_sample=false 未被错误修改。
6. 是否没有运行 affine.exe。
7. 是否没有运行 solver、runtime probe、debugger、emulator。
8. 是否没有新建重复 IDA/Ghidra runner。
9. 是否二选一处理 detailed evidence：
   A. 若提交 detailed evidence，是否真的提交单个 bounded JSON，并登记 latest_artifacts 与 latest_artifacts_v2；
   B. 若不提交 detailed evidence，是否从 report.generated_artifacts、artifact_index.latest_artifacts_v2、artifact_index.latest_artifacts、summary.evidence_artifacts 中全部移除该路径。
10. 是否没有把不存在于 GitHub 的 path 标记为 freshness=current。
11. 是否将 solver_hints.direct_strcmp 降级为 static_compare_api_context_only 或 business_compare_not_confirmed。
12. 是否保留下一步建议为 _main_0 / scanf 后数据流 targeted_static_reextract。
13. 是否更新 artifact_index 中所有被改动 artifact 的 sha256/size_bytes/modified_at。
14. 是否没有上传原始样本。
15. 是否没有提交 full solve_reports。
16. 是否没有修改 .codex-skills。
17. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
18. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_detailed_evidence_consistency_rework_v1。
```

---

## 6. Implementation Scope

允许修改：

```text
project_state/local_reverse_affine_ida_summary.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

仅当选择提交 bounded detailed evidence 时，允许新增：

```text
solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
```

如果提交该文件，必须满足：

```text
1. 只提交该单个 JSON，不提交 full solve_reports。
2. 文件不包含本地绝对路径。
3. 文件不包含原始样本 bytes。
4. 文件不包含敏感本地环境信息。
5. artifact_index.latest_artifacts 增加 local_reverse_ida_evidence_affine_8cfebe03。
6. artifact_index.latest_artifacts_v2 增加 local_reverse_ida_evidence_affine_8cfebe03，freshness=current，source_run=round_20260604_affine_detailed_evidence_consistency_rework_v1。
```

如果不提交该文件，必须完成：

```text
1. 从 codex_execution_report.md 的 generated_artifacts 中移除 solve_reports/.../affine_ida_evidence.json。
2. 从 artifact_index.latest_artifacts_v2 删除 local_reverse_ida_evidence_affine_8cfebe03。
3. 确保 artifact_index.latest_artifacts 中也没有 local_reverse_ida_evidence_affine_8cfebe03。
4. 从 local_reverse_affine_ida_summary.json 的 evidence_artifacts 中移除该路径，或改为 []。
5. 在 report 中明确说明：detailed evidence 未提交，当前可审计证据为 project_state/local_reverse_affine_ida_summary.json。
```

`solver_hints` 建议修正为：

```json
[
  {
    "kind": "static_compare_api_context_only",
    "reason": "IDA found compare API context, but current compare site is CRT/heap-related and business compare is not confirmed"
  },
  {
    "kind": "console_input_flow_candidate",
    "reason": "_main_0 puts/scanf input flow recovered near 0x401054 and 0x401065"
  }
]
```

不得删除已有可用静态证据；只修正不可审计 artifact 引用和偏强结论。

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

本轮原则上不应修改 Python 代码。如果修改 Python 代码，必须说明为什么 JSON/Markdown 返工无法完成目标。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPT`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_ida_summary.json 缺失。
2. local_reverse_affine_ida_summary.json 无法解析为 JSON。
3. 修复 detailed evidence 引用需要运行 affine.exe。
4. 修复 detailed evidence 引用需要 solver、runtime probe、debugger、emulator。
5. 修复 detailed evidence 引用需要上传原始样本。
6. 修复 detailed evidence 引用需要提交 full solve_reports。
7. detailed evidence 文件包含本地绝对路径、原始样本 bytes 或敏感环境信息，但又无法改为 summary-only。
8. artifact_index 更新会覆盖或删除既有 current local_reverse 证据。
```

完成条件：

```text
1. 不存在任何 GitHub 404 path 被 report/artifact_index/summary 当作 current evidence 引用。
2. detailed evidence 要么真实提交并登记，要么彻底从 report/artifact_index/summary 中移除。
3. solver_hints 不再暗示业务 direct_strcmp 已确认。
4. 下一步建议仍聚焦 _main_0 / scanf 后数据流 targeted_static_reextract。
5. report/pytest 与 decision_20260604_affine_detailed_evidence_consistency_rework_v1 对齐。
6. required tests 全部记录且 Exit code 0。
7. 未运行样本、solver、runtime probe、debugger、emulator。
8. 未上传原始样本，未提交 full solve_reports。
```

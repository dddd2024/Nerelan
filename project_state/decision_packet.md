```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260604_affine_ida_static_export_rework_v1",
  "round_id": "round_20260604_affine_ida_static_export_rework_v1",
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

上一轮 `decision_20260604_affine_ida_static_export_v1` 生成了：

```text
project_state/local_reverse_affine_ida_summary.json
```

但审计结论是 `REWORK_REQUIRED`。本轮目标：**只修复 affine IDA 静态导出产物的一致性和报告可信度，不重新求解、不运行样本、不运行 runtime probe。**

必须修复三类问题：

```text
1. local_reverse_affine_ida_summary.json 中 relative_path 写错：
   当前错误值：返向课程2024春补考03/affine.exe
   必须修正：逆向课程2024春补考03/affine.exe

2. codex_execution_report.md 声称生成：
   solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
   但该文件未提交到 GitHub，artifact_index 也未登记。必须修复 generated_artifacts 与 artifact_index 的一致性。

3. 上一轮报告把 CRT/debug heap 相关函数（sub_407A90、__CrtDbgReport、__heap_alloc_dbg 等）表述为验证函数候选，存在过度解释。必须降级为 CRT/debug-support noise 或 low-priority static candidates，并把下一步收敛到 _main_0 中 scanf 后的数据流。
```

本轮不是重新 IDA 导出，不是求解 affine，不生成 candidate，不输出 flag。

---

## 2. Current Evidence

当前 `task_packet.json` 仍可能保留旧 samplereverse 派生任务；它只是 advisory。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

上一轮报告摘要：

```text
report_id: report_20260604_affine_ida_static_export_v1
based_on_decision_id: decision_20260604_affine_ida_static_export_v1
status: SUCCESS
generated_artifacts:
  - project_state/local_reverse_affine_ida_summary.json
  - solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json
```

当前已确认的问题：

```text
1. project_state/local_reverse_affine_ida_summary.json 存在。
2. artifact_index.latest_artifacts.local_reverse_affine_ida_summary 已存在。
3. artifact_index.latest_artifacts_v2.local_reverse_affine_ida_summary 已标记 freshness=current。
4. solve_reports/tool_artifacts/local_reverse_affine_ida_static_export_v1/affine_8cfebe03/affine_ida_evidence.json 未在 GitHub 中找到。
5. artifact_index 未登记 local_reverse_ida_evidence_affine_8cfebe03 或等价 detailed evidence key。
6. local_reverse_affine_ida_summary.json 的 relative_path 写错为 返向课程2024春补考03/affine.exe。
```

当前可保留的 affine IDA summary 静态字段包括：

```text
sample_id: affine_8cfebe03
sha256: 8cfebe030f2d9fced106881e5aa6b2d81d162d31230dd3418b8fc3b15a5ef659
size_bytes: 196688
analysis_mode: ida_static_export
executed_sample: false
ida_status: success
hexrays_available: true
entry_point: 0x401520
functions_count: 282
strings_count: 220
```

上一轮 summary 中 `_main_0` 附近已有输入线索：

```text
0x401054: _puts, ref_strings: please input a string:
0x401065: _scanf, ref_strings: please input a string: | %s
```

上一轮 summary 中 `sub_407A90`、`__CrtDbgReport`、`__heap_alloc_dbg` 等更像 CRT/debug heap/memory-check 逻辑，不能作为高置信业务验证函数。

`negative_results.json` 仍禁止：old sample_solver blind search、只扩大 beam/budget、提交 full solve_reports、重复旧 runtime/probe 失败方向。本轮不涉及这些方向。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 affine.exe。
2. 不运行 solver。
3. 不生成 candidate、flag 或最终答案。
4. 不运行 debugger、runtime probe、Frida、OllyDbg、x64dbg、emulator。
5. 不重新运行 IDA，除非仅为校验现有 summary/evidence 是否存在且不扩大范围。
6. 不上传 E:\reverse 原始样本。
7. 不复制 affine.exe 到仓库。
8. 不提交 full solve_reports 目录。
9. 不修改 .codex-skills。
10. 不新建重复 IDA runner 或 Ghidra runner。
11. 不新建 affine 专用硬编码 solver。
12. 不把 affine 单题结论写入长期 skill。
13. 不回到 old sample_solver blind search。
14. 不扩大 beam/budget/bruteforce。
15. 不把 CRT/debug heap 函数表述为高置信业务验证函数。
16. 不把 IDA 静态证据等同于 runtime validation。
17. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt。
```

允许：

```text
1. 编辑 project_state/local_reverse_affine_ida_summary.json 的元数据和解释字段。
2. 编辑 artifact_index.json 中本轮相关 artifact 的 sha256/size_bytes/modified_at/provenance。
3. 编辑 codex_execution_report.md，修正 generated_artifacts 与实际提交文件一致。
4. 编辑 pytest_result.txt。
5. 若 bounded detailed evidence 文件确实存在且体积可控、无本地绝对路径或样本泄露，可提交并登记该单个 evidence JSON。
6. 若不提交 detailed evidence，则必须从 report.generated_artifacts 中移除该路径，并说明只提交 summary。
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

必要时检查：

```text
reverse_agent/tool_runners.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/ida_scripts/collect_evidence.py
tests/test_project_state.py
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
4. 是否修正 relative_path 为 逆向课程2024春补考03/affine.exe。
5. 是否确认 sample_id、sha256、size_bytes 未被错误修改。
6. 是否确认 executed_sample=false。
7. 是否没有运行 affine.exe。
8. 是否没有运行 solver、runtime probe、debugger、emulator。
9. 是否没有新建重复 IDA/Ghidra runner。
10. 是否处理 detailed evidence artifact 与 generated_artifacts 的一致性。
11. 如果提交 detailed evidence，是否已登记 artifact_index.latest_artifacts 和 latest_artifacts_v2。
12. 如果不提交 detailed evidence，是否已从 report.generated_artifacts 移除并说明原因。
13. 是否将 CRT/debug heap 函数降级为 noise 或 low-priority static candidates。
14. 是否把下一步建议收敛到 _main_0 / scanf 后数据流的 targeted_static_reextract。
15. 是否更新 artifact_index 中 local_reverse_affine_ida_summary 的 sha256/size_bytes/modified_at。
16. 是否没有上传原始样本。
17. 是否没有提交 full solve_reports。
18. 是否没有修改 .codex-skills。
19. pytest_result.txt 是否记录真实测试命令且全部 Exit code 0。
20. codex_report_summary.based_on_decision_id 是否等于 decision_20260604_affine_ida_static_export_rework_v1。
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

但必须满足：

```text
1. 只提交该单个 bounded JSON，不提交 full solve_reports。
2. 文件不包含本地绝对路径。
3. 文件不包含原始样本 bytes。
4. 文件不包含敏感本地环境信息。
5. artifact_index.latest_artifacts_v2 登记 freshness=current、source_run=round_20260604_affine_ida_static_export_rework_v1、sha256、size_bytes、modified_at、sample_id=affine_8cfebe03。
```

`local_reverse_affine_ida_summary.json` 建议最小修复：

```text
relative_path: 逆向课程2024春补考03/affine.exe
analysis_mode: ida_static_export
executed_sample: false
ida_status: success
```

并新增或修正解释字段，例如：

```json
{
  "noise_or_low_priority_functions": [
    {
      "function": "sub_407A90",
      "reason": "CRT/debug heap memory-check context; not confirmed affine validation logic"
    },
    {
      "function": "__CrtDbgReport",
      "reason": "CRT debug reporting function; not business validation logic"
    },
    {
      "function": "__heap_alloc_dbg",
      "reason": "CRT debug heap allocator; not business validation logic"
    }
  ],
  "recommended_next_action": "targeted_static_reextract_main_input_flow",
  "recommended_next_focus": "_main_0 scanf/post-input data flow near 0x401054 and 0x401065",
  "limitations": [
    "IDA static export found CRT/debug-support noise; core affine transform or final compare not yet confirmed",
    "IDA static evidence is not runtime validation"
  ]
}
```

不得删除已有可用静态证据；只修正错误路径和过度解释。

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

本轮原则上不应修改 Python 代码。如果修改了 `tool_runners.py`、`local_reverse_ida_summary.py` 或 `ida_scripts/collect_evidence.py`，必须说明为什么返工不能通过 project_state JSON 修复完成，并运行相关测试。

所有 required commands 必须 Exit code 0。若任何命令失败，`codex_execution_report.md` 不得写 `SUCCESS/ACCEPT`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. project_state/local_reverse_affine_ida_summary.json 缺失。
2. local_reverse_affine_ida_summary.json 无法解析为 JSON。
3. 修正 relative_path 会导致 sample_id/sha256/size_bytes 与现有 inventory 冲突。
4. 需要运行 affine.exe 才能完成返工。
5. 需要 solver、runtime probe、debugger、emulator 才能完成返工。
6. 需要上传原始样本才能完成返工。
7. 需要提交 full solve_reports 才能完成返工。
8. detailed evidence 文件包含本地绝对路径、原始样本 bytes 或其他不应提交内容，且 report 又无法改为 summary-only。
9. artifact_index 更新会覆盖或删除既有 current local_reverse 证据。
```

完成条件：

```text
1. relative_path 已修正为 逆向课程2024春补考03/affine.exe。
2. report.generated_artifacts 与实际提交文件一致。
3. detailed evidence 要么被有界提交并登记，要么从 generated_artifacts 中移除并说明原因。
4. CRT/debug heap 相关函数不再被描述为高置信业务验证函数。
5. 下一步建议聚焦 _main_0 / scanf 后数据流 targeted_static_reextract。
6. artifact_index 中 local_reverse_affine_ida_summary 的 sha256/size_bytes/modified_at 已更新。
7. report/pytest 与 decision_20260604_affine_ida_static_export_rework_v1 对齐。
8. required tests 全部记录且 Exit code 0。
9. 未运行样本、solver、runtime probe、debugger、emulator。
10. 未上传原始样本，未提交 full solve_reports。
```

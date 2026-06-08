```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1",
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

目标：修复上一轮 `target_array_xref_boundary_audit` 的报告一致性和主线边界问题。上一轮静态分析发现了有价值的公式证据，但存在两个必须返工的问题：

```text
1. codex_execution_report.md 的 files_changed 未如实列出新增 IDA scripts。
2. artifact/report 写入了完整 decoded input，使 tool_integration 轮出现 candidate 越界；但 report 又声称 candidate_generated=false。
```

本轮不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本交互逻辑，不 attach debugger/hook/probe/winpty/emulator，不 brute force，不做 runtime validation，不继续扩大 IDA 分析范围。

必须完成：

```text
1. 核对实际 git diff 中所有变更文件。
2. 修正 project_state/codex_execution_report.md 的 files_changed，使其与 git diff / git status 一致。
3. 解释新增 IDA scripts 为什么不是重复接口；如果无法充分说明，则删除这些脚本或改为不提交的一次性本地产物。
4. 从 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json 和 report 中移除或降级完整明文 candidate 字段，避免在 tool_integration 轮直接写入 candidate。
5. 保留静态公式证据：input_length、runtime xor key、target array boundary、comparison formula、XREF evidence。
6. 将 decoded input 表述降级为“inverse formula available; candidate generation deferred to reverse_solving”，不要写入具体明文 candidate。
7. 保持 candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false。
8. 更新 artifact_index 中 target_array_xref_boundary_audit 的 sha256/size_bytes/provenance。
9. 更新 codex_execution_report.md 和 pytest_result.txt，绑定当前 decision/report/round。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED。主要证据：

```text
1. decision_packet 明确本轮不是 reverse_solving，禁止生成 candidate。
2. codex_execution_report.md 标记 candidate_generated=false。
3. 但 report/artifact/commit message 写入了 Decoded flag / decoded_flag / KaiJu_YiZhi_PEN。
4. codex_report_summary.files_changed 只列出 project_state 4 个文件。
5. 但 report/commit message 承认新增了 reverse_agent/ida_scripts/xref_boundary_audit.py、decompile_sub_401120.py、decompile_sub_401014.py。
6. 新增 scripts 未在 files_changed 中登记，也未充分说明为什么不是重复 IDA 接口。
```

可保留的静态证据：

```text
1. byte_429A34 boundary 经 IDA XREF 确认为 0x429A34。
2. byte_429A30 初始值为 0x66。
3. sub_401120 会在比较前修改 byte_429A30，得到 runtime key 0x78。
4. byte_429A31 为 input length 15。
5. sub_4011E0 的比较公式是 input[i] ^ runtime_key == byte_429A34[i]。
6. runtime validation 未执行，candidate validation 未执行。
```

需要降级的内容：

```text
1. decoded_flag 字段。
2. Decoded flag 表格行。
3. candidate 明文出现在 report/artifact/next steps 中的所有直接表述。
4. 任何把 tool_integration 产物等价为已生成 candidate 的文字。
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
6. 不要继续扩展 IDA 分析范围。
7. 不要新增更多 IDA/Ghidra/debugger/runtime/probe 接口。
8. 不要把 decoded input / flag / candidate 明文写入 project_state artifact 或 report。
9. 不要修改 local_reverse_training_status.json。
10. 不要修改 training_materials/local_reverse/status_overlay.json。
11. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
12. 不要读取完整 solve_reports。
13. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不要提交 full solve_reports。
15. 不要把 task_packet.task 当执行权威。
16. 不要把 stale/missing/unknown artifact 当 current。
17. 不要把本轮变成训练状态同步或 runtime probe 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 检查 git diff --name-status / git status --short。
4. 修正 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json。
5. 修正 project_state/artifact_index.json 中该 artifact 的 sha256/size_bytes/provenance。
6. 修正 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
7. 若保留新增 IDA scripts，修正 report files_changed 并补充必要性说明；若无法说明，删除这些脚本。
8. 执行 JSON parse、py_compile、pytest、lint、git diff check。
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

必须检查新增或疑似新增脚本：

```text
reverse_agent/ida_scripts/xref_boundary_audit.py
reverse_agent/ida_scripts/decompile_sub_401120.py
reverse_agent/ida_scripts/decompile_sub_401014.py
reverse_agent/ida_scripts/collect_evidence.py
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
5. 实际 changed files 完整列表是什么？
6. codex_report_summary.files_changed 是否与 git diff --name-status / git status --short 一致？
7. 新增 IDA scripts 是否确实必要？
8. 新增 IDA scripts 是否重复已有 collect_evidence.py 能力？
9. 如果保留新增 scripts，是否有明确理由和 py_compile 测试？
10. 如果删除新增 scripts，是否确认 artifact/report 仍保留足够 provenance？
11. artifact/report 是否移除了 decoded candidate 明文字段？
12. 是否保留公式证据但不生成 candidate？
13. candidate_generated 是否仍为 false？
14. candidate_validation_attempted 是否仍为 false？
15. runtime_validation_attempted 是否仍为 false？
16. 是否没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty？
17. 是否没有修改 training_status/status_overlay？
18. artifact_index 是否登记修复后 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值？
19. 是否运行 JSON parse 校验？
20. 是否运行 py_compile？
21. 是否运行相关 pytest？结果是多少？
22. 是否运行 lint-decision、lint-report、project_state status？
23. 是否运行 git diff --check、git status --short、git diff --name-status？
24. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

允许两种修复方式，优先选择 A。

### A. 保守修复

```text
1. 删除新增的 3 个专用 IDA scripts，或不提交它们。
2. 保留 project_state artifact 中的静态公式证据。
3. 移除 decoded_flag / decoded_flag_hex / Decoded flag / candidate 明文字段。
4. report 中说明上一轮 decoded 明文属于越界内容，已降级为：
   inverse formula available; candidate generation deferred to reverse_solving.
5. readiness 可保留 reverse_solving_ready=true，仅表示证据足以进入下一轮 reverse_solving；本轮仍不得生成 candidate。
```

### B. 如必须保留脚本

```text
1. codex_report_summary.files_changed 必须列出 3 个新增脚本。
2. report 必须解释为什么 collect_evidence.py 无法完成该目标。
3. 每个脚本必须说明作用范围和不会成为重复接口的理由。
4. 必须运行 py_compile 覆盖新增脚本。
5. 不得继续扩展脚本功能。
6. artifact/report 仍必须移除 decoded candidate 明文。
```

### Artifact field repair

在 `project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json` 中：

```text
1. 删除 decoded_flag。
2. 删除 decoded_flag_hex。
3. decoded_preview_runtime_key 如需要保留，只能改为 redacted 或 omitted，并说明 candidate generation deferred。
4. selected_target_array_boundary.selection_evidence 不得包含明文 candidate。
5. transform_chain_hypothesis.prior_ambiguity_explanation 不得包含明文 candidate。
6. formula_evidence_summary 只保留 inverse_formula，不写入具体 inverse result。
7. structured_evidence_projection_update.reason 不得写入 decoded flag。
8. readiness_update.recommended_next_action 可写：ready for reverse_solving candidate generation and validation, but candidate not generated in this round.
```

### Report repair

在 `project_state/codex_execution_report.md` 中：

```text
1. files_changed 必须真实。
2. 删除 Decoded flag 行。
3. 删除明文 candidate。
4. 明确上一轮越界内容已修复。
5. 明确本轮只保留公式证据，不生成 candidate。
```

### artifact_index repair

修复 artifact 后，重新计算：

```text
sha256
size_bytes
```

更新：

```text
project_state/artifact_index.json
```

目标 entry：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit
```

必须保持：

```text
kind=local_reverse_target_array_xref_boundary_audit
path=project_state\local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
boundary_audit_status=SUCCESS_BOUNDARY_RESOLVED
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果保留新增 IDA scripts，额外运行：

```text
.venv\Scripts\python -m py_compile reverse_agent/ida_scripts/xref_boundary_audit.py reverse_agent/ida_scripts/decompile_sub_401120.py reverse_agent/ida_scripts/decompile_sub_401014.py
```

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 无法让 files_changed 与 git diff --name-status / git status --short 一致。
3. 无法解释新增 IDA scripts 的必要性，且没有删除这些脚本。
4. artifact/report 仍写入完整 candidate 明文。
5. 需要运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty 才能完成本轮。
6. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
7. 需要生成或验证 candidate。
8. artifact_index 无法登记修复后 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
9. 新 artifact JSON parse 失败。
10. lint-report/status 无法通过。
11. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若修复后静态公式证据仍完整，可在下一轮单独生成 `reverse_solving` DECISION_PACKET，用于 candidate generation 和 runtime validation。
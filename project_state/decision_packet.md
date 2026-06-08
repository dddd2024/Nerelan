```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1",
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

目标：修复上一轮返工仍残留的问题，只做二次返工，不重新分析样本，不生成 candidate，不运行样本，不做 runtime validation。

必须完成：

```text
1. 从 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json 中彻底移除完整明文 candidate。
2. 将 project_state/artifact_index.json 中 target_array_xref_boundary_audit 的 source_run 更新为当前返工 round。
3. 将 project_state/pytest_result.txt 绑定当前 decision/report/round。
4. 如果保留新增 IDA scripts，补充并记录 py_compile 覆盖。
5. 更新 project_state/codex_execution_report.md，绑定当前 decision/report/round，并记录上述修复。
6. 重新计算 target_array_xref_boundary_audit artifact 的 sha256 与 size_bytes，并同步 artifact_index。
```

本轮不得进入 reverse_solving。不得生成 candidate、不得验证 candidate、不得运行样本交互逻辑、不得 attach debugger/hook/probe/winpty/emulator、不得 brute force、不得 runtime validation。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮返工审计结论仍为 REWORK_REQUIRED，原因是：

```text
1. artifact 中 selected_target_array_boundary.decoded_preview_runtime_key 仍保留完整明文 candidate。
2. artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.source_run 仍指向旧 round。
3. pytest_result.txt 仍绑定旧 round。
4. 保留新增 IDA scripts，但 pytest_result/report 未记录新增脚本 py_compile。
```

已经修复过、可以保留的内容：

```text
1. codex_execution_report.md 的 files_changed 已包含 7 个文件，包括 3 个新增 IDA scripts。
2. report 主体中的 decoded output 已改为 REDACTED。
3. formula_evidence_summary.decoded_flag 与 decoded_flag_hex 已改为 REDACTED。
4. 静态公式证据可以保留：input_length=15、runtime xor key=0x78、target_array_bytes_hex、comparison_formula、inverse_formula、XREF evidence。
5. reverse_solving_ready=true 可以保留为下一轮主线建议，但本轮不能生成 candidate。
```

需要继续修复：

```text
1. decoded_preview_runtime_key 必须改为 REDACTED 或 omitted。
2. 任何字段中不得包含完整 candidate 明文。
3. artifact_index.source_run 必须改为当前 round。
4. pytest_result.txt 必须改为当前 round，并列出新增 IDA scripts 的 py_compile。
5. codex_execution_report.md 必须记录这些修复和测试。
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
3. 搜索并移除 artifact/report 中的完整 candidate 明文残留。
4. 修正 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json。
5. 修正 project_state/artifact_index.json 中该 artifact 的 sha256/size_bytes/source_run。
6. 修正 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
7. 对保留的新增 IDA scripts 运行 py_compile。
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

必须检查新增脚本：

```text
reverse_agent/ida_scripts/xref_boundary_audit.py
reverse_agent/ida_scripts/decompile_sub_401120.py
reverse_agent/ida_scripts/decompile_sub_401014.py
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
5. artifact 中是否仍存在完整明文 candidate？必须明确搜索结果。
6. decoded_preview_runtime_key 是否已 REDACTED 或 omitted？
7. formula_evidence_summary.decoded_flag / decoded_flag_hex 是否仍为 REDACTED 或删除？
8. artifact_index.source_run 是否已更新为当前 round？
9. artifact_index sha256/size_bytes 是否重新计算并同步？
10. pytest_result.txt 是否绑定当前 decision/report/round？
11. 是否记录新增 IDA scripts 的 py_compile？
12. candidate_generated 是否仍为 false？
13. candidate_validation_attempted 是否仍为 false？
14. runtime_validation_attempted 是否仍为 false？
15. 是否没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty？
16. 是否没有修改 training_status/status_overlay？
17. 是否运行 JSON parse 校验？
18. 是否运行 py_compile？
19. 是否运行相关 pytest？结果是多少？
20. 是否运行 lint-decision、lint-report、project_state status？
21. 是否运行 git diff --check、git status --short、git diff --name-status？
22. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Redact remaining plaintext

在 `project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json` 中：

```text
1. selected_target_array_boundary.decoded_preview_runtime_key 必须改为 REDACTED 或删除。
2. formula_evidence_summary.decoded_flag 必须保持 REDACTED 或删除。
3. formula_evidence_summary.decoded_flag_hex 必须保持 REDACTED 或删除。
4. selected_target_array_boundary.selection_evidence 不得包含完整 candidate 明文。
5. transform_chain_hypothesis.prior_ambiguity_explanation 不得包含完整 candidate 明文。
6. structured_evidence_projection_update.reason 不得包含完整 candidate 明文。
7. readiness_update.recommended_next_action 不得包含完整 candidate 明文。
```

允许保留：

```text
input_length=15
xor_key_runtime=0x78
target_array_bytes_hex
comparison_formula
inverse_formula
15/15 printable ASCII
candidate generation deferred to reverse_solving
```

### Phase B — Fix artifact_index provenance

修复 artifact 后，重新计算并更新：

```text
sha256
size_bytes
modified_at
```

目标 entry：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit
```

必须设置：

```text
source_run=round_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1
```

必须保持：

```text
kind=local_reverse_target_array_xref_boundary_audit
path=project_state\local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
freshness=current
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
boundary_audit_status=SUCCESS_BOUNDARY_RESOLVED
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

### Phase C — Fix report and pytest_result

更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必须绑定：

```text
decision_id=decision_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1
report_id=report_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1
round_id=round_20260608_cpp2_883e67b9_target_array_redaction_provenance_rework_v1
```

report 必须说明：

```text
1. 已修复 decoded_preview_runtime_key 残留明文。
2. 已修复 artifact_index.source_run。
3. 已修复 pytest_result stale/mismatch。
4. 已对新增 IDA scripts 运行 py_compile。
5. 本轮仍未生成 candidate，未 runtime validation。
```

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
1. artifact 任意字段仍保留完整明文 candidate。
2. pytest_result.txt 没有绑定当前 round。
3. artifact_index.source_run 仍指向旧 round。
4. 保留新增 IDA scripts 但没有 py_compile 记录。
5. 需要运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty 才能完成本轮。
6. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
7. 需要生成或验证 candidate。
8. artifact_index 无法登记修复后 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
9. 新 artifact JSON parse 失败。
10. lint-report/status 无法通过。
11. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若修复后静态公式证据仍完整，可在下一轮单独生成 `reverse_solving` DECISION_PACKET，用于 candidate generation 和 runtime validation。
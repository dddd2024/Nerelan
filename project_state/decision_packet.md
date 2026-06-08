```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_candidate_artifact_index_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_candidate_artifact_index_rework_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **reverse_solving**，但本轮只做上一轮 candidate validation 的产物登记返工。

目标：修复 `cpp2_883e67b9` candidate validation 轮的 artifact schema、artifact_index provenance 和 pytest_result 测试目标问题。

本轮不要重新生成 candidate，不要重新运行样本，不要重新 runtime validation，不要执行 IDA/Ghidra/static extraction。只修复受控产物登记、schema 和测试记录。

必须完成：

```text
1. 扩充 project_state/local_reverse_cpp2_883e67b9_candidate_validation.json，使其包含上一轮 decision_packet 要求字段。
2. 将 target_sha256 从空字符串修正为已验证样本 SHA256：
   883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
3. 在 artifact_index.latest_artifacts_v2 中登记 local_reverse_cpp2_883e67b9_candidate_validation 的结构化 entry。
4. 不要使用新 artifact_metadata 块替代 latest_artifacts_v2；如当前已有 artifact_metadata，可保留兼容信息，但必须补齐 latest_artifacts_v2。
5. 更新 artifact_index 中真实 sha256 / size_bytes / modified_at。
6. 更新 pytest_result.txt，使 JSON parse validation 解析新 artifact：
   project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
7. 更新 codex_execution_report.md，绑定当前 rework decision/report/round。
8. 不扩大 local_reverse_training_status/status_overlay 修改；若保持已解决状态，只说明这是复用上一轮 VALIDATED_SUCCESS 证据。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED，但有有效验证线索：

```text
1. candidate 生成和 runtime validation 方向正确。
2. candidate 从 current 公式 evidence 计算：input[i] = byte_429A34[i] ^ 0x78。
3. candidate=KaiJu_YiZhi_PEN，candidate_hex=4b61694a755f59695a68695f50454e，length=15。
4. validation 使用 existing local_reverse_console_validator。
5. stdout 中出现 Good work，exit_code=0，validation_status=VALIDATED_SUCCESS。
6. report 声称没有 IDA/Ghidra/static extraction、没有 brute force、没有新框架。
7. local_reverse_training_status 已被最小更新为 solved，但登记链条尚未闭合。
```

上一轮阻断问题：

```text
1. project_state/local_reverse_cpp2_883e67b9_candidate_validation.json 字段过少，缺少 artifact_kind、decision_id、round_id、identity_verified、formula_evidence_summary、candidate_generation、negative_results_checked、capability_check、status_update_recommendation 等字段。
2. candidate_validation artifact 中 target_sha256 为空字符串。
3. artifact_index 只写入 latest_artifacts 和 artifact_metadata，没有按要求写入 latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation。
4. pytest_result 的 JSON parse validation 解析的是 target_array_xref_boundary_audit 旧 artifact，而不是 candidate_validation 新 artifact。
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复旧 samplereverse 失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要重新运行样本。
2. 不要重新 runtime validation。
3. 不要重新生成 candidate。
4. 不要执行 IDA/Ghidra/static extraction。
5. 不要 brute force、dictionary search、fuzz、beam search、topN search、扩大 timeout/budget。
6. 不要新建 runtime/harness/debugger/probe 接口。
7. 不要修改 .codex-skills。
8. 不要提交根目录工具 dump。
9. 不要修改无关 solver production code。
10. 不要扩大 local_reverse_training_status 或 status_overlay 修改。
11. 不要读取完整 solve_reports。
12. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
13. 不要把 task_packet.task 当执行权威。
14. 不要把 stale/missing/unknown artifact 当 current。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 current 的 cpp2_883e67b9 target_array_xref_boundary_audit、candidate 和 candidate_validation artifacts。
3. 扩充 candidate_validation artifact schema。
4. 更新 artifact_index.latest_artifacts_v2 与 sha256/size_bytes/modified_at。
5. 更新 codex_execution_report.md 和 pytest_result.txt。
6. 运行 JSON parse、py_compile、pytest、lint、git diff check。
7. 复用上一轮 runtime validation 证据，但必须明确本轮没有重跑 runtime validation。
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
project_state/local_reverse_cpp2_883e67b9_candidate.json
project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
project_state/local_reverse_training_status.json
```

必须核对但不要扩大修改：

```text
training_materials/local_reverse/status_overlay.json
```

必要时检查 artifact/index 相关代码和测试：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否仍为 reverse_solving，但本轮是否仅做 artifact/index rework？
3. task_packet 是否仅为 advisory？
4. 是否没有重新生成 candidate？
5. 是否没有重新运行样本或 runtime validation？
6. 是否没有执行 IDA/Ghidra/static extraction？
7. 是否没有 brute force/dictionary/fuzz/beam/topN/budget 扩展？
8. candidate_validation artifact 是否补齐 artifact_kind、decision_id、round_id、identity_verified、target_sha256、formula_evidence_summary、candidate_generation、validation、negative_results_checked、capability_check、status_update_recommendation 等字段？
9. target_sha256 是否为 883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8？
10. artifact 是否明确 validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1？
11. artifact 是否明确 runtime_validation_not_rerun_in_this_rework=true？
12. artifact_index.latest_artifacts_v2 是否包含 local_reverse_cpp2_883e67b9_candidate_validation 结构化 entry？
13. latest_artifacts_v2 entry 是否有 kind/path/freshness/source_run/sample_id/relative_path/candidate_generated/candidate_validation_attempted/runtime_validation_attempted/validation_status/sha256/size_bytes？
14. pytest_result 的 JSON parse validation 是否解析 candidate_validation artifact？
15. codex_report_summary.files_changed 是否与实际 git diff --name-status 一致？
16. 是否没有提交根目录工具 dump？
17. 是否没有修改 .codex-skills？
18. 是否没有扩大 training_status/status_overlay 修改？
19. 是否运行 JSON parse 校验？
20. 是否运行 py_compile？
21. 是否运行相关 pytest？结果是多少？
22. 是否运行 lint-decision、lint-report、project_state status？
23. 是否运行 git diff --check、git status --short、git diff --name-status？
24. git diff 是否只包含允许文件？
```

---

## 6. Artifact Schema Requirements

`project_state/local_reverse_cpp2_883e67b9_candidate_validation.json` 必须至少包含：

```text
schema_version
mainline=reverse_solving
artifact_kind=local_reverse_candidate_validation
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
identity_verified=true
target_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
round_id=round_20260608_cpp2_883e67b9_candidate_artifact_index_rework_v1
decision_id=decision_20260608_cpp2_883e67b9_candidate_artifact_index_rework_v1
source_artifacts 包含 target_array_xref_boundary_audit 与 candidate artifact，且标记 freshness/source_run
formula_evidence_summary
candidate_generation
candidate_plaintext
candidate_hex
candidate_length
validation
negative_results_checked
capability_check
status_update_recommendation
candidate_generated=true
candidate_validation_attempted=true
runtime_validation_attempted=true
training_status_modified=true
status_overlay_modified=false
```

可以复用上一轮 runtime validation 证据，但必须明确：

```text
validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
runtime_validation_not_rerun_in_this_rework=true
```

---

## 7. artifact_index Requirements

必须登记到：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation
```

字段至少包含：

```text
kind=local_reverse_candidate_validation
path=project_state\local_reverse_cpp2_883e67b9_candidate_validation.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_candidate_artifact_index_rework_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
candidate_generated=true
candidate_validation_attempted=true
runtime_validation_attempted=true
validation_status=VALIDATED_SUCCESS
sha256=<真实值>
size_bytes=<真实值>
modified_at=<当前更新时间>
```

可以保留 `latest_artifacts` 兼容旧字段，但不能只登记旧字段或 `artifact_metadata`。

---

## 8. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_candidate_validation.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

---

## 9. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. candidate_validation artifact 仍缺少 decision_id / round_id / artifact_kind / identity_verified / target_sha256。
2. artifact_index.latest_artifacts_v2 仍没有 candidate_validation entry。
3. pytest_result 仍解析旧 target_array_xref_boundary_audit artifact 而不是 candidate_validation artifact。
4. 需要重新运行样本或 runtime validation。
5. 需要重新生成 candidate。
6. 需要执行 IDA/Ghidra/static extraction。
7. 需要 brute force/dictionary/fuzz/beam/topN/budget 扩展。
8. lint-report/status 失败。
9. git diff 包含根目录工具 dump、.codex-skills 动态事实或无关代码变更。
10. 需要扩大 training_status/status_overlay 修改。
```

完成后不要继续推进新样本或工程重构。若该返工通过，cpp2_883e67b9 可视为 runtime validated solved，下一轮可单独规划训练集 summary/status sync 或能力复盘。
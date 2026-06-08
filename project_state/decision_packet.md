```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1",
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

本轮主线是 **reverse_solving**，但只做 candidate validation artifact 与 artifact_index 的精确 schema 返工。

目标：修复 `cpp2_883e67b9` candidate validation artifact 与 `artifact_index.latest_artifacts_v2` 中仍存在的字段名和值不匹配问题。

本轮只修字段和登记，不重新生成 candidate，不重新运行样本，不重新 runtime validation，不执行 IDA/Ghidra/static extraction。

必须完成：

```text
1. 将 project_state/local_reverse_cpp2_883e67b9_candidate_validation.json 中 artifact_kind 精确改为：
   local_reverse_candidate_validation

2. 补齐 candidate_validation artifact 缺失字段：
   identity_verified=true
   source_artifacts 包含 target_array_xref_boundary_audit 与 candidate artifact，并记录 freshness/source_run
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

3. 保留并明确：
   validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
   runtime_validation_not_rerun_in_this_rework=true

4. 修复 artifact_index.latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation：
   kind=local_reverse_candidate_validation
   source_run=round_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1
   sample_id=cpp2_883e67b9
   relative_path=逆向课程2024春02/CPP2.exe
   candidate_generated=true
   candidate_validation_attempted=true
   runtime_validation_attempted=true
   validation_status=VALIDATED_SUCCESS
   sha256=<真实值>
   size_bytes=<真实值>
   modified_at=<当前更新时间>

5. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 REWORK_REQUIRED。已修复的部分：

```text
1. pytest_result 已改为解析 candidate_validation artifact。
2. target_sha256 已从空字符串修复为：
   883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
3. artifact_index.latest_artifacts_v2 已出现 candidate_validation entry。
4. 本轮未重新运行样本、未重新 runtime validation、未执行 IDA/Ghidra/static extraction。
```

仍未修复的阻断问题：

```text
1. artifact_kind 当前仍是 candidate_validation，不是 local_reverse_candidate_validation。
2. artifact 缺少 identity_verified、candidate_generation、validation、negative_results_checked、capability_check、status_update_recommendation 等 required fields。
3. artifact_index.latest_artifacts_v2 entry 中 kind 当前仍是 candidate_validation。
4. artifact_index.latest_artifacts_v2 entry 中 source_run 当前不是本轮 round。
5. artifact_index.latest_artifacts_v2 entry 缺少 sample_id、relative_path、candidate_generated、candidate_validation_attempted、runtime_validation_attempted、validation_status 等 required fields。
```

可复用上一轮 runtime validation 证据：

```text
candidate=KaiJu_YiZhi_PEN
candidate_hex=4b61694a755f59695a68695f50454e
candidate_length=15
validation_status=VALIDATED_SUCCESS
success_token=Good work
stdout_tail contains Good work
validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
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
10. 不要修改 local_reverse_training_status.json。
11. 不要修改 training_materials/local_reverse/status_overlay.json。
12. 不要读取完整 solve_reports。
13. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不要把 task_packet.task 当执行权威。
15. 不要把 stale/missing/unknown artifact 当 current。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 current 的 cpp2_883e67b9 target_array_xref_boundary_audit、candidate 和 candidate_validation artifacts。
3. 精确修正 candidate_validation artifact schema。
4. 精确修正 artifact_index.latest_artifacts_v2 entry。
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

必须核对但不要修改：

```text
training_materials/local_reverse/status_overlay.json
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
2. mainline 是否仍为 reverse_solving，但本轮是否仅做 exact schema rework？
3. task_packet 是否仅为 advisory？
4. 是否没有重新生成 candidate？
5. 是否没有重新运行样本或 runtime validation？
6. 是否没有执行 IDA/Ghidra/static extraction？
7. 是否没有 brute force/dictionary/fuzz/beam/topN/budget 扩展？
8. artifact_kind 是否精确为 local_reverse_candidate_validation？
9. candidate_validation artifact 是否补齐 identity_verified、source_artifacts、candidate_generation、validation、negative_results_checked、capability_check、status_update_recommendation？
10. candidate_validation artifact 是否包含 candidate_plaintext、candidate_hex、candidate_length？
11. candidate_validation artifact 是否包含 candidate_generated=true、candidate_validation_attempted=true、runtime_validation_attempted=true、training_status_modified=true、status_overlay_modified=false？
12. artifact 是否明确 validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1？
13. artifact 是否明确 runtime_validation_not_rerun_in_this_rework=true？
14. artifact_index.latest_artifacts_v2 entry 的 kind 是否精确为 local_reverse_candidate_validation？
15. artifact_index.latest_artifacts_v2 entry 的 source_run 是否精确为当前 round？
16. artifact_index.latest_artifacts_v2 entry 是否包含 sample_id、relative_path、candidate_generated、candidate_validation_attempted、runtime_validation_attempted、validation_status、sha256、size_bytes、modified_at？
17. pytest_result 的 JSON parse validation 是否解析 candidate_validation artifact？
18. codex_report_summary.files_changed 是否与实际 git diff --name-status 一致？
19. 是否没有提交根目录工具 dump？
20. 是否没有修改 .codex-skills？
21. 是否没有修改 training_status/status_overlay？
22. 是否运行 JSON parse 校验？
23. 是否运行 py_compile？
24. 是否运行相关 pytest？结果是多少？
25. 是否运行 lint-decision、lint-report、project_state status？
26. 是否运行 git diff --check、git status --short、git diff --name-status？
27. git diff 是否只包含允许文件？
```

---

## 6. Exact Artifact Requirements

`project_state/local_reverse_cpp2_883e67b9_candidate_validation.json` 必须至少包含以下键和值：

```text
schema_version=1
mainline=reverse_solving
artifact_kind=local_reverse_candidate_validation
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
identity_verified=true
target_sha256=883e67b92321ce10780e5a80f431a5784e9d91bcfb19642798c57e07006299e8
decision_id=decision_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1
round_id=round_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1
validation_reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
runtime_validation_not_rerun_in_this_rework=true
candidate_plaintext=KaiJu_YiZhi_PEN
candidate_hex=4b61694a755f59695a68695f50454e
candidate_length=15
candidate_generated=true
candidate_validation_attempted=true
runtime_validation_attempted=true
training_status_modified=true
status_overlay_modified=false
```

必须包含对象：

```text
source_artifacts:
  - local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit with freshness/source_run
  - local_reverse_cpp2_883e67b9_candidate with freshness/source_run

formula_evidence_summary:
  formula
  target_array_start_va
  xor_key_runtime
  input_length
  target_array_bytes_hex

candidate_generation:
  method=current_formula_inverse
  formula=input[i] = byte_429A34[i] ^ 0x78
  generated_in_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
  regenerated_in_this_round=false

validation:
  method=console_runtime_validation
  tool=local_reverse_console_validator
  status=VALIDATED_SUCCESS
  success_token=Good work
  return_code=0
  stdout_tail
  stderr_tail
  reused_from_round=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
  rerun_in_this_round=false

negative_results_checked:
  checked=true
  repeated_forbidden_direction=false
  notes

capability_check:
  existing_validator_used=true
  new_runtime_interface_created=false
  ida_ghidra_static_extraction_rerun=false

status_update_recommendation:
  training_status_already_updated=true
  status_overlay_update_needed=false
  next_action
```

---

## 7. Exact artifact_index Requirements

必须修复：

```text
latest_artifacts_v2.local_reverse_cpp2_883e67b9_candidate_validation
```

该 entry 必须至少包含：

```text
kind=local_reverse_candidate_validation
path=project_state\local_reverse_cpp2_883e67b9_candidate_validation.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_candidate_schema_exact_rework_v1
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

可以保留 `latest_artifacts` 兼容旧字段和 artifact_metadata，但不能只依赖它们。

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
1. artifact_kind 仍不是 local_reverse_candidate_validation。
2. candidate_validation artifact 仍缺少 identity_verified / candidate_generation / validation / negative_results_checked / capability_check / status_update_recommendation。
3. latest_artifacts_v2 entry 缺少 sample_id / relative_path / candidate_generated / candidate_validation_attempted / runtime_validation_attempted / validation_status。
4. latest_artifacts_v2 entry 的 kind 不是 local_reverse_candidate_validation。
5. latest_artifacts_v2 entry 的 source_run 不是当前 round。
6. 需要重新运行样本或 runtime validation。
7. 需要重新生成 candidate。
8. 需要执行 IDA/Ghidra/static extraction。
9. lint-report/status 失败。
10. git diff 包含根目录工具 dump、.codex-skills 动态事实或无关代码变更。
11. 修改了 local_reverse_training_status.json 或 status_overlay.json。
```

完成后不要继续推进新样本或工程重构。若该返工通过，cpp2_883e67b9 可视为 runtime validated solved，下一轮可单独规划训练集 summary/status sync 或能力复盘。
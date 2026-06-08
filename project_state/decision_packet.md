```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_guardrails_v1",
  "round_id": "round_20260608_solver_profile_dispatch_guardrails_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **engineering_branch**。

目标：对上一轮 `solver_profile_dispatch_integration` 做小步 guardrail 加固，消除审计中标记的两个限制：

```text
1. profile-normalized evidence 的 profile 与 recover_constraints 的 classification 不一致时，必须阻断，不允许静默改写或按另一个 profile 求解。
2. profile-normalized evidence 的 freshness 不是 current 时，必须阻断，不允许从 stale/missing/unknown evidence 派生 candidate。
```

本轮不是解新题，不推进 `cpp2_883e67b9`，不运行任何本地样本，不做 runtime validation，不调用 IDA/Ghidra/debugger/hook/emulator/probe/winpty。只允许修改 dispatch/profile guardrail、synthetic-only 测试、审计 artifact、artifact_index、Codex report 和 pytest_result。

必须完成：

```text
1. 在 profile-normalized dispatch 边界加入 profile/classification mismatch 阻断。
2. 在 profile-normalized dispatch 边界加入 freshness=current 强校验。
3. 保持已有三类 profile dispatch 正常：
   - xor_array_table_compare
   - bytewise_reversible_transform_table_compare
   - digit_mod_affine_transform_compare
4. 保持旧 profile 行为不回退：
   - api_assisted_password_write_and_compare
   - bounded_input_range_hash_output_increment_compare
   - sha256_hex_compare_with_post_hash_character_adjustment
5. 增加 synthetic-only 测试覆盖 mismatch、stale/missing/unknown freshness、nested normalized_profile_evidence mismatch。
6. 生成 guardrail audit artifact，并更新 artifact_index。
```

建议产出：

```text
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_constraint_recovery.py
tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 Codex 判断只需修改 `local_reverse_constraint_recovery.py` 而不改 `local_reverse_solver_profiles.py`，可以这样做，但必须在报告里说明 guardrail 所在边界以及为什么不会影响纯 helper 层。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮报告为：

```text
report_id=report_20260608_solver_profile_dispatch_integration_v1
round_id=round_20260608_solver_profile_dispatch_integration_v1
based_on_decision_id=decision_20260608_solver_profile_dispatch_integration_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
mainline=engineering_branch
```

上一轮报告记录：没有真实样本 candidate、没有 candidate validation、没有 runtime validation、没有 debugger/emulator、没有训练状态或 status overlay 修改。files_changed 包括 `local_reverse_solver_profiles.py`、`local_reverse_constraint_recovery.py`、dispatch 测试、audit artifact、artifact_index、report 和 pytest_result。

上一轮测试记录为：

```text
pytest_result.status=PASSED
pytest target: tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
result: 172 passed
lint-decision: PASS
lint-report: PASS
project_state status: CONSUMED_BY_SUCCESS_REPORT
```

上一轮 dispatch integration audit artifact 已登记为 current：

```text
kind=local_reverse_solver_profile_dispatch_integration_audit
path=project_state\local_reverse_solver_profile_dispatch_integration_audit.json
freshness=current
source_run=round_20260608_solver_profile_dispatch_integration_v1
mainline=engineering_branch
candidate_generation_performed=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

上一轮已集成 profile：

```text
xor_array_table_compare
bytewise_reversible_transform_table_compare
digit_mod_affine_transform_compare
```

现有代码状态：

```text
reverse_agent/local_reverse_constraint_recovery.py:
  - recover_constraints 在 classification 属于 PROFILE_NORMALIZED_CLASSIFICATIONS 时分发到 recover_profile_normalized_constraints。
  - recover_profile_normalized_constraints 调用 _normalized_profile_payload 后调用 solve_normalized_profile。
  - helper 返回 SOLVED 且 candidate_generated 时，会生成 validation_status=unverified 的 candidate record。
  - 当前审计发现：没有显式拒绝 profile/classification mismatch；没有显式拒绝 non-current freshness。

reverse_agent/local_reverse_solver_profiles.py:
  - ProfileNormalizedEvidence.from_mapping 接收 profile/profile_evidence/source_artifact/source_run/freshness/provenance_notes。
  - solve_normalized_profile 会拒绝 unsupported profile 和 unknown transform_kind。
  - 当前审计发现：freshness 字段被记录但未作为阻断条件。
```

当前 training summary 仍为：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver 和 project_state lint/status 机制。本轮只做工程 guardrail，不调用成熟逆向工具，不重写反汇编/反编译/调试能力。

`negative_results.json` 主要约束旧 `samplereverse` 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill。本轮 skill_profiles 只能使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要继续推进 cpp2_883e67b9 求解。
2. 不要运行任何 E:\reverse 样本。
3. 不要执行 candidate、negative control 或 runtime validation。
4. 不要 attach debugger / hook / emulator / probe / winpty。
5. 不要调用 IDA/Ghidra 或读取样本二进制。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要修改 local_reverse_training_status.json 中 solved/blocked/inventory 状态。
8. 不要修改 training_materials/local_reverse/status_overlay.json。
9. 不要把 KEEP_DREAM、WeKnowItOk、10013、hookapi 写死进 production solver 或 dispatch。
10. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
11. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
12. 不要重写成熟工具已有的反汇编/反编译能力。
13. 不要读取完整 solve_reports。
14. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不要提交 full solve_reports。
16. 不要把 task_packet.task 当作执行权威。
17. 不要把本轮变成训练状态同步、新样本求解轮、工具动态验证轮或真实 artifact 提取轮。
18. 不要通过真实 artifact 临时解析 candidate 来通过测试。
19. 不要把 stale/missing/unknown freshness 当作 current。
20. 不要在 profile 与 classification 不一致时静默选择任一方继续求解。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮新增的 solver profile helper、dispatch、测试和 audit artifact。
3. 读取现有 constraint recovery / string solver / runtime validator 代码以避免重复实现。
4. 用 synthetic normalized evidence fixtures 测试 guardrail。
5. 新增或更新纯函数/dispatch 单元测试。
6. 生成 solver profile dispatch guardrails audit artifact。
7. 更新 artifact_index 注册新 audit artifact。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
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

project_state/local_reverse_solver_profile_dispatch_integration_audit.json
project_state/local_reverse_training_status.json

reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runtime.py

tests/test_local_reverse_solver_profile_dispatch.py
tests/test_local_reverse_solver_profiles.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/evidence.py
reverse_agent/static_feature_extractor.py
reverse_agent/simple_static_patterns.py
tests/ 中已有 local_reverse / constraint recovery 相关测试
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
E:\reverse 样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 engineering_branch？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不解新题？
5. 是否确认未推进 cpp2_883e67b9？
6. 上一轮 dispatch integration 是否为本轮基础？
7. 是否修复 profile/classification mismatch 的静默求解风险？
8. mismatch 时具体 blocked_reason 是什么？
9. 是否修复 stale/missing/unknown freshness 仍可生成 candidate 的风险？
10. non-current freshness 时具体 blocked_reason 是什么？
11. nested normalized_profile_evidence 的 profile mismatch 是否也会阻断？
12. 当前三类 profile 的 current evidence happy path 是否仍通过？
13. unknown transform_kind 是否仍 blocked，且不执行表达式字符串？
14. 现有 api/hash/sha constraint recovery 行为是否未回退？
15. 是否没有运行样本？
16. 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？
17. 是否没有调用 IDA/Ghidra 或读取二进制？
18. 是否没有修改 training_status/status_overlay？
19. 是否没有读取 full solve_reports？
20. 是否没有在 production code 中硬编码真实 candidate？
21. 是否新增或更新了 synthetic-only 测试？
22. pytest_result 是否包含当前 decision_id/report_id/round_id？
23. artifact_index 是否登记 guardrails audit artifact？
24. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — define strict normalized evidence guardrails

在最小边界实现 guardrail。优先位置：

```text
reverse_agent/local_reverse_constraint_recovery.py
```

可选位置：

```text
reverse_agent/local_reverse_solver_profiles.py
```

要求：

```text
1. profile-normalized dispatch 必须要求 effective_profile == classification。
2. effective_profile 可以来自 top-level evidence.profile，也可以来自 nested evidence.normalized_profile_evidence.profile。
3. 如果 top-level profile、nested profile、classification 任意形成冲突，必须返回 BLOCKED，不生成 candidate。
4. 建议 blocked_reason 使用 PROFILE_CLASSIFICATION_MISMATCH 或 BLOCKED:PROFILE_CLASSIFICATION_MISMATCH，但必须在测试和 audit 中固定。
5. 不允许用 nested.setdefault("profile", classification) 掩盖显式 mismatch。
```

### Phase B — enforce freshness=current before candidate generation

要求：

```text
1. profile-normalized dispatch 派生 candidate 前必须确认 normalized_payload.freshness == "current"。
2. freshness in {"stale", "missing", "unknown", ""} 必须 blocked，不生成 candidate。
3. 如果字段缺失，按 unknown 处理，不允许默认 current。
4. 建议 blocked_reason 使用 NON_CURRENT_PROFILE_EVIDENCE 或 BLOCKED:NON_CURRENT_PROFILE_EVIDENCE，但必须在测试和 audit 中固定。
5. constraints 中应保留 source_artifact/source_run/freshness/provenance_notes，便于审计。
```

### Phase C — preserve existing behavior

不得改变：

```text
1. invert_xor_array_table / invert_bytewise_transform_table / invert_digit_mod_affine_table 的纯函数 happy path。
2. unknown transform_kind 返回 BLOCKED，不执行任意表达式。
3. api_assisted_password_write_and_compare 的基础 synthetic regression。
4. bounded_input_range_hash_output_increment_compare 和 sha256_hex_compare_with_post_hash_character_adjustment 的 dispatch 顺序和 blocked 行为。
5. runtime_allowed=false 时不调用 probe_runner。
```

如果需要重构，必须是局部重构，不得新建 runtime/debugger/IDA/Ghidra 接口。

### Phase D — tests

新增或扩展 synthetic-only 测试。至少覆盖：

```text
1. top-level evidence.profile != classification 时 blocked，不生成 candidate。
2. nested normalized_profile_evidence.profile != classification 时 blocked，不生成 candidate。
3. freshness=stale 时 blocked，不生成 candidate。
4. freshness=missing 时 blocked，不生成 candidate。
5. freshness=unknown 或字段缺失时 blocked，不生成 candidate。
6. freshness=current 且 profile 匹配时三类 profile happy path 仍能生成 unverified synthetic candidate。
7. unknown transform_kind 仍 blocked，且不执行表达式字符串。
8. 旧 api_assisted_password_write_and_compare synthetic regression 不回退。
9. production module 和 dispatch module 不包含 KEEP_DREAM / WeKnowItOk / 10013 / hookapi。
10. runtime_allowed=false 的 synthetic path 不调用 probe_runner。
```

允许运行：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

### Phase E — audit artifact

生成：

```text
project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json
```

内容至少包括：

```text
schema_version
generated_at
mainline=engineering_branch
round_id=round_20260608_solver_profile_dispatch_guardrails_v1
decision_id=decision_20260608_solver_profile_dispatch_guardrails_v1
source_previous_report=report_20260608_solver_profile_dispatch_integration_v1
source_previous_audit=project_state\local_reverse_solver_profile_dispatch_integration_audit.json
task_packet_authority=advisory_only
guardrails_added:
  - profile_classification_mismatch_blocks_without_candidate
  - non_current_freshness_blocks_without_candidate
mismatch_blocked_reason
non_current_freshness_blocked_reason
profiles_regression_checked
legacy_profile_regression_check
runtime_actions_performed=false
candidate_generation_performed=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
full_solve_reports_read=false
sample_binary_read=false
ida_or_ghidra_invoked=false
debugger_hook_emulator_probe_winpty_used=false
new_runtime_or_debugger_interface_created=false
production_hardcode_check
tests_added_or_updated
next_recommended_mainline
next_recommended_action
```

`candidate_generation_performed=false` 指真实样本 candidate 生成未执行；synthetic unit test candidate 不算真实样本求解。

### Phase F — artifact_index registration

将新 audit artifact 注册到：

```text
artifact_index.latest_artifacts["local_reverse_solver_profile_dispatch_guardrails_audit"]
artifact_index.latest_artifacts_v2["local_reverse_solver_profile_dispatch_guardrails_audit"]
artifact_index.artifact_refs["local_reverse_solver_profile_dispatch_guardrails_audit"]
```

`latest_artifacts_v2` 至少包括：

```text
kind=local_reverse_solver_profile_dispatch_guardrails_audit
path=project_state\local_reverse_solver_profile_dispatch_guardrails_audit.json
freshness=current
source_run=round_20260608_solver_profile_dispatch_guardrails_v1
sample_id=multi_solved_profile_dispatch_guardrails
mainline=engineering_branch
candidate_generation_performed=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

不要删除或覆盖上一轮：

```text
local_reverse_solver_profile_dispatch_integration_audit
local_reverse_solver_engineering_recovery_audit
```

### Phase G — report

`codex_execution_report.md` 顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_solver_profile_dispatch_guardrails_v1",
  "round_id": "round_20260608_solver_profile_dispatch_guardrails_v1",
  "based_on_decision_id": "decision_20260608_solver_profile_dispatch_guardrails_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "mainline": "engineering_branch",
  "sample_id": "multi_solved_profile_dispatch_guardrails",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

如果没有真实运行测试，不能写 SUCCESS/ACCEPTED。

---

## 7. Tests

必须至少运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

`project_state/pytest_result.txt` 必须记录：

```text
decision_id=decision_20260608_solver_profile_dispatch_guardrails_v1
report_id=report_20260608_solver_profile_dispatch_guardrails_v1
round_id=round_20260608_solver_profile_dispatch_guardrails_v1
status=PASSED|FAILED
```

必须能从 pytest_result 中看出 guardrail 测试真实执行过。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. Codex 需要运行真实样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
3. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
4. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
5. 需要把真实 candidate 写进 production code 才能通过测试。
6. 无法在 mismatch 时阻断 candidate generation。
7. 无法在 non-current freshness 时阻断 candidate generation。
8. pytest_result 无法绑定当前 decision_id/report_id/round_id。
9. artifact_index 无法登记 guardrails audit artifact。
10. 发现上一轮 dispatch integration report/pytest/artifact_index 与当前状态冲突，导致本轮依据不可靠。
```

完成后不要继续下一轮样本求解。下一步建议只能写入报告，不要自行扩大到 `tool_integration` 或 `reverse_solving`。

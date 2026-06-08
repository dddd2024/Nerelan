```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_integration_v1",
  "round_id": "round_20260608_solver_profile_dispatch_integration_v1",
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

目标：把上一轮已经新增并测试通过的纯函数 solver profile helper 接入 `local_reverse_constraint_recovery` 的分发边界，形成 **profile-normalized evidence -> solver profile helper -> SolverProfileResult/candidate record** 的最小工程闭环。

本轮不是解新题，不推进 `cpp2_883e67b9` 求解，不运行任何本地样本，不做 runtime validation，不调用 IDA/Ghidra/debugger/hook/emulator/winpty。

必须完成：

```text
1. 审计上一轮新增的 reverse_agent/local_reverse_solver_profiles.py 是否适合作为纯 helper 层。
2. 定义最小 profile-normalized evidence contract，用于三类已回收 profile：
   - xor_array_table_compare
   - bytewise_reversible_transform_table_compare
   - digit_mod_affine_transform_compare
3. 在 local_reverse_constraint_recovery 的分发边界接入这三类 profile，但只接受 normalized evidence；缺失 normalized evidence 时必须 BLOCKED/PARTIAL，不能猜测或解析真实样本。
4. 保持现有 api_assisted_password_write_and_compare、bounded_input_range_hash_output_increment_compare、sha256_hex_compare_with_post_hash_character_adjustment 行为不回退。
5. 增加 synthetic-only 单元测试，覆盖新 profile dispatch、缺证据 blocking、旧 profile 不回退和 production hardcode guard。
```

建议产出：

```text
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_constraint_recovery.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_constraint_recovery.py 或新增 tests/test_local_reverse_solver_profile_dispatch.py
project_state/local_reverse_solver_profile_dispatch_integration_audit.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 Codex 判断不应直接修改 `local_reverse_constraint_recovery.py`，可以新增一个薄 adapter 模块，例如 `reverse_agent/local_reverse_solver_profile_dispatch.py`，但必须在报告中说明原因，并保证没有重复 runtime/debugger/IDA/Ghidra 接口。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论：`report_20260608_solver_engineering_recovery_foundation_v1` 已被接受。该轮主线为 `engineering_branch`，执行结果为 `SUCCESS / ACCEPTED`，未执行样本、candidate validation、runtime validation、debugger、hook、emulator、probe 或 winpty。

上一轮新增能力：

```text
reverse_agent/local_reverse_solver_profiles.py:
  - SolverProfileResult
  - invert_xor_array_table
  - invert_bytewise_transform_table
  - invert_digit_mod_affine_table

tests/test_local_reverse_solver_profiles.py:
  - synthetic XOR reverse-index 测试
  - synthetic bytewise bit-swap 测试
  - synthetic digit modular affine 测试
  - ambiguous / no-inverse 测试
  - production hardcode guard
```

上一轮测试记录：

```text
pytest_result.status=PASSED
pytest target: tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
result: 164 passed
lint-decision: PASS
lint-report: PASS
project_state status: decision consumed by success report
```

当前 training summary 仍按状态文件记录为：

```text
sample_count=29
solved=4
blocked=4
needs_triage=0
inventory_only=21
```

已 solved 样本仍仅作为 profile 回收来源，不作为本轮 candidate 生成目标：

```text
cpp1_7b504c54 -> WeKnowItOk
cpp1_bcbd9979 -> hookapi
cpp2_2f64e68d -> 10013
cpp2_32f1713e -> KEEP_DREAM
```

已有工程化状况：

```text
1. api_assisted_password_write_and_compare:
   已有初步分发：recover_constraints -> recover_cpp1_constraints。

2. xor_array_table_compare:
   已有纯 helper，但尚未接入 constraint recovery profile dispatch。

3. digit_mod_affine_transform_compare:
   已有纯 helper，但尚未接入 constraint recovery profile dispatch。

4. bytewise_reversible_transform_table_compare:
   已有纯 helper，但尚未接入 constraint recovery profile dispatch。
```

`artifact_index.json` 已登记 `local_reverse_solver_engineering_recovery_audit` 为 current。新一轮需要登记新的 dispatch integration audit artifact，不要覆盖上一轮 audit 的语义。

工具能力边界：项目已有 IDA-guided solver、runtime probe、constraint recovery、string solver 和 project_state lint/status 机制。本轮只做工程分发和纯函数测试，不调用成熟逆向工具，不重写反汇编/反编译/调试能力。

`negative_results.json` 主要约束旧 `samplereverse` 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮 skill_profiles 只能使用该 profile。

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
17. 不要把本轮变成训练状态同步、新样本求解轮或工具动态验证轮。
18. 不要从真实 artifact 中临时硬解析 candidate 来通过测试。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取上一轮新增的 solver profile helper、测试和 audit artifact。
3. 读取现有 constraint recovery / string solver / runtime validator 代码以避免重复实现。
4. 用 synthetic normalized evidence fixtures 测试 dispatch。
5. 新增或更新纯函数/dispatch 单元测试。
6. 生成 solver profile dispatch integration audit artifact。
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

project_state/local_reverse_solver_engineering_recovery_audit.json
project_state/local_reverse_training_status.json

reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runtime.py

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
6. 是否确认上一轮 solver helper 已存在并作为本轮基础？
7. 是否定义了 profile-normalized evidence contract？
8. 三类新 profile 是否已接入 dispatch 或薄 adapter？
9. 缺失 normalized evidence 时是否 BLOCKED/PARTIAL，而不是猜测 candidate？
10. 现有 api/hash/sha constraint recovery 行为是否未回退？
11. 是否没有运行样本？
12. 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？
13. 是否没有调用 IDA/Ghidra 或读取二进制？
14. 是否没有修改 training_status/status_overlay？
15. 是否没有读取 full solve_reports？
16. 是否没有在 production code 中硬编码真实 candidate？
17. 是否新增或更新了 synthetic-only 测试？
18. pytest_result 是否包含当前 decision_id/report_id/round_id？
19. artifact_index 是否登记 solver profile dispatch integration audit artifact？
20. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — profile-normalized evidence contract

在合适位置定义最小 contract。优先保持轻量，不引入数据库、队列或重型 schema 系统。

可以放在：

```text
reverse_agent/local_reverse_solver_profiles.py
```

或新增薄 adapter：

```text
reverse_agent/local_reverse_solver_profile_dispatch.py
```

contract 建议字段：

```text
profile: str
profile_evidence: dict
source_artifact: str
source_run: str
freshness: current|stale|missing|unknown
provenance_notes: list[str]
```

三类 profile 的 `profile_evidence` 最小字段建议：

```text
xor_array_table_compare:
  array_a: list[int]
  array_b: list[int]
  target: list[int]
  reverse_a: bool
  encoding: str

bytewise_reversible_transform_table_compare:
  target: list[int]
  transform_kind: str
  transform_params: dict
  domain: list[int] or bounded_domain_name
  encoding: str

 digit_mod_affine_transform_compare:
  target: list[int|string]
  a: int
  b: int
  modulus: int
  offset: int
  domain: list[int]
```

只实现已经测试可控的 transform_kind。若 `transform_kind` 未知，返回 `BLOCKED`，不要动态执行任意表达式字符串。

### Phase B — dispatch integration

在 `local_reverse_constraint_recovery.py` 中接入新 profile，或通过 adapter 由 `recover_constraints` 调用。

要求：

```text
1. classification == xor_array_table_compare 时，读取 normalized evidence 并调用 invert_xor_array_table。
2. classification == bytewise_reversible_transform_table_compare 时，读取 normalized evidence 并调用 invert_bytewise_transform_table。
3. classification == digit_mod_affine_transform_compare 时，读取 normalized evidence 并调用 invert_digit_mod_affine_table。
4. helper 返回 SOLVED 时，转换为现有 candidates 结构，validation_status=unverified。
5. helper 返回 PARTIAL/BLOCKED 时，不生成 candidate，并填充 blocked_reason/next_action。
6. 若 evidence 不含 normalized profile_evidence，必须返回 missing_profile_normalized_evidence 类 blocked reason。
7. 不改变 runtime_allowed=false 时的行为；本轮测试不得触发 validate_candidates。
```

不得把真实 solved candidate 写入代码。不得从真实 artifact 文件里硬解析样本专用字段来绕过 normalized evidence contract。

### Phase C — tests

新增或扩展测试，优先使用 synthetic fixtures。

测试至少覆盖：

```text
1. recover_constraints 能通过 xor_array_table_compare normalized evidence 生成一个 unverified synthetic candidate。
2. recover_constraints 能通过 digit_mod_affine_transform_compare normalized evidence 生成一个 unverified synthetic candidate。
3. recover_constraints 能通过 bytewise_reversible_transform_table_compare normalized evidence 生成一个 unverified synthetic candidate。
4. 缺失 profile_evidence 时返回 blocked，不生成 candidate。
5. unknown transform_kind 返回 blocked，不执行任意表达式。
6. 旧 profile api_assisted_password_write_and_compare 的基础行为不回退。
7. production module 和 dispatch module 不包含 KEEP_DREAM / WeKnowItOk / 10013 / hookapi。
8. runtime_allowed=false 的 synthetic path 不调用 probe_runner。
```

允许继续运行：

```text
pytest -q tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
```

并新增/运行相关 dispatch 测试，例如：

```text
pytest -q tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
```

### Phase D — audit artifact

生成：

```text
project_state/local_reverse_solver_profile_dispatch_integration_audit.json
```

内容至少包括：

```text
schema_version
mainline=engineering_branch
round_id=round_20260608_solver_profile_dispatch_integration_v1
decision_id=decision_20260608_solver_profile_dispatch_integration_v1
source_previous_report=report_20260608_solver_engineering_recovery_foundation_v1
profiles_integrated
normalized_evidence_contract
unsupported_profile_behavior
legacy_profile_regression_check
runtime_actions_performed=false
candidate_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
full_solve_reports_read=false
new_runtime_or_debugger_interface_created=false
production_hardcode_check
next_recommended_mainline
next_recommended_action
generated_at
```

`profiles_integrated` 至少记录：

```text
xor_array_table_compare
bytewise_reversible_transform_table_compare
digit_mod_affine_transform_compare
```

### Phase E — artifact_index registration

将新 audit artifact 注册到：

```text
artifact_index.latest_artifacts["local_reverse_solver_profile_dispatch_integration_audit"]
artifact_index.latest_artifacts_v2["local_reverse_solver_profile_dispatch_integration_audit"]
artifact_index.artifact_refs["local_reverse_solver_profile_dispatch_integration_audit"]
```

`latest_artifacts_v2` 至少包括：

```text
kind=local_reverse_solver_profile_dispatch_integration_audit
path=project_state\\local_reverse_solver_profile_dispatch_integration_audit.json
freshness=current
source_run=round_20260608_solver_profile_dispatch_integration_v1
sample_id=multi_solved_profile_dispatch_integration
mainline=engineering_branch
candidate_generation_performed=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

### Phase F — report

`codex_execution_report.md` 顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_solver_profile_dispatch_integration_v1",
  "round_id": "round_20260608_solver_profile_dispatch_integration_v1",
  "based_on_decision_id": "decision_20260608_solver_profile_dispatch_integration_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "mainline": "engineering_branch",
  "sample_id": "multi_solved_profile_dispatch_integration",
  "identity_verified": true,
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [
    "project_state/local_reverse_solver_profile_dispatch_integration_audit.json"
  ]
}
```

注意：本轮可能在 synthetic test 中生成 synthetic candidate 字符串，但 `candidate_generated` 字段应表示是否为真实样本生成 candidate；必须保持 false。

---

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

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

如果测试文件命名不同，必须在报告中说明实际测试路径，但必须覆盖同等断言。

`pytest_result.txt` 必须包含：

```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_profile_dispatch_integration_v1",
  "report_id": "report_20260608_solver_profile_dispatch_integration_v1",
  "round_id": "round_20260608_solver_profile_dispatch_integration_v1",
  "status": "PASSED|FAILED|PARTIAL",
  "tests_ran": []
}
```

若测试失败，不要标记 SUCCESS；必须在 report 中标记 `FAILED` 或 `PARTIAL`，并给出具体失败点。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `PARTIAL`：

```text
1. decision_meta / report summary / pytest summary 无法对齐。
2. registry 中 active skill 与 skill_profiles 不匹配。
3. 需要运行真实样本、runtime validation、debugger、hook、emulator、probe、winpty 才能继续。
4. 需要读取 E:\reverse 样本或完整 solve_reports 才能继续。
5. 新 profile dispatch 无法在 normalized evidence 缺失时安全 BLOCKED。
6. 新代码需要硬编码 KEEP_DREAM、WeKnowItOk、10013、hookapi 才能通过测试。
7. 旧 api/hash/sha constraint recovery 测试出现回退。
8. artifact_index 无法注册新 audit artifact。
9. project_state lint-decision 或 lint-report 不通过。
10. git diff 出现 scope 外文件，例如 training status、status overlay、.codex-skills 或 full solve_reports。
```

完成条件：

```text
1. 新 profile dispatch/adapter 支持三类 normalized evidence。
2. 缺证据/未知 transform 能安全 BLOCKED，不猜测 candidate。
3. synthetic-only tests 通过。
4. 旧 constraint recovery 行为不回退。
5. 新 audit artifact 已生成并登记为 current。
6. codex_execution_report.md 与 pytest_result.txt 对齐当前 decision_id/round_id。
```

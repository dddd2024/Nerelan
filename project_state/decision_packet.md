```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_solver_engineering_recovery_foundation_v1",
  "round_id": "round_20260608_solver_engineering_recovery_foundation_v1",
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

目标：对已经 solved 的本地逆向样本做 **solver 工程化回收**，把单样本 artifact 中已经验证过的解题模式整理成可复用 solver profile 的最小工程基础。

本轮不是解新题，不推进 `cpp2_883e67b9` 求解，不运行任何样本，不做 runtime validation。

必须完成：

```text
1. 审计当前 solved 样本中哪些题型已有 solver，哪些只是 artifact/handoff。
2. 建立 solver profile 回收清单。
3. 为至少 3 类已解题型定义工程化 profile contract：
   - xor_array_table_compare
   - bytewise_reversible_transform_table_compare
   - digit_mod_affine_transform_compare
4. 复用现有 solver/constraint recovery 入口，避免重复造轮子。
5. 增加纯函数级单元测试，不依赖本地 E:\reverse 样本运行。
```

建议产出：

```text
project_state/local_reverse_solver_engineering_recovery_audit.json
reverse_agent/local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profiles.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 Codex 判断不应新建 `local_reverse_solver_profiles.py`，可以改为扩展现有 `reverse_agent/local_reverse_constraint_recovery.py`，但必须在报告里说明原因。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

最新审计结论：`report_20260607_cpp2_883e67b9_bounded_loop_evidence_extraction_v1` 可接受但有限制。该轮只做 bounded static evidence extraction，状态是 `PARTIAL / ACCEPTED_WITH_LIMITATIONS`。

当前 training summary：

```text
sample_count=29
solved=4
blocked=4
inventory_only=21
```

已 solved 样本包括：

```text
cpp1_7b504c54 -> WeKnowItOk
cpp1_bcbd9979 -> hookapi
cpp2_2f64e68d -> 10013
cpp2_32f1713e -> KEEP_DREAM
```

已知 solver 工程化现状：

```text
1. api_assisted_password_write_and_compare:
   已有初步工程化。
   local_reverse_constraint_recovery.py 已分发到 recover_cpp1_constraints。

2. xor_array_table_compare:
   cpp1_7b504c54 已通过 artifact 解出 WeKnowItOk。
   当前主要是单样本 xor_handoff，还没有通用 solver profile。

3. digit_mod_affine_transform_compare:
   cpp2_2f64e68d 已通过 oracle-backed 逆推得到 10013。
   当前主要是 raw_input_candidate_from_oracle artifact，还没有通用 solver profile。

4. bytewise_reversible_transform_table_compare:
   cpp2_32f1713e 已通过 bit-swap + target table 解出 KEEP_DREAM。
   当前主要是 targeted_static_solving artifact，还没有通用 solver profile。
```

现有代码中 `local_reverse_constraint_recovery.py` 只正式分发了：

```text
api_assisted_password_write_and_compare
bounded_input_range_hash_output_increment_compare
sha256_hex_compare_with_post_hash_character_adjustment
```

不包含 `xor_array_table_compare`、`digit_mod_affine_transform_compare`、`bytewise_reversible_transform_table_compare`。这说明 solved artifact 已经领先于工程化 solver。

已有相关能力：

```text
- reverse_agent/local_reverse_constraint_recovery.py: 现有 constraint recovery 分发与 candidate validation 结构。
- reverse_agent/local_reverse_ida_guided_solver.py: 现有 IDA-guided profile 分类与候选派生结构。
- reverse_agent/local_reverse_string_solver.py: 现有字符串候选构建与 runtime validation 结构。
- reverse_agent/local_reverse_runtime.py: 现有 runtime probe；本轮只能读取，不允许运行。
- tests/test_project_state.py: 现有 project_state 测试基线。
```

工具边界：本轮是工程化回收，不调用 IDA/Ghidra/debugger/runtime，不读样本二进制。成熟工具接口只作为已有能力检查对象，不新建重复接口。

negative_results 主要约束旧 `samplereverse` 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮 skill_profiles 只能使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要继续推进 cpp2_883e67b9 求解。
2. 不要运行任何 E:\reverse 样本。
3. 不要执行 candidate 或 negative control。
4. 不要做 runtime validation。
5. 不要 attach debugger / hook / emulator / probe / winpty。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要修改 local_reverse_training_status.json 中任何 solved/blocked/inventory 状态。
8. 不要修改 training_materials/local_reverse/status_overlay.json。
9. 不要把 KEEP_DREAM、WeKnowItOk、10013、hookapi 写死进 production solver。
10. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
11. 不要新建重复的 IDA/Ghidra/debugger/runtime interface。
12. 不要重写成熟工具已有的反汇编/反编译能力。
13. 不要读取完整 solve_reports。
14. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不要提交 full solve_reports。
16. 不要把 task_packet.task 当作执行权威。
17. 不要把本轮变成训练状态同步或新样本求解轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 4 个 solved 样本对应的 bounded artifact。
3. 读取现有 solver / constraint recovery / runtime validator 代码。
4. 新增纯函数级 solver profile helper。
5. 新增单元测试，使用 synthetic fixtures，不依赖真实样本运行。
6. 生成 solver engineering recovery audit artifact。
7. 更新 artifact_index 注册新 audit artifact。
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

project_state/local_reverse_training_status.json
project_state/local_reverse_constraint_recovery_result.json

project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
project_state/local_reverse_cpp2_32f1713e_targeted_static_solving.json
project_state/local_reverse_cpp2_32f1713e_keep_dream_runtime_validation.json

reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runtime.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/evidence.py
reverse_agent/static_feature_extractor.py
reverse_agent/simple_static_patterns.py
tests/ 中已有 local_reverse / solver 相关测试
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
3. 是否确认本轮不是 reverse_solving，不解新题？
4. task_packet 是否仅为 advisory？
5. 当前 solved 样本数量是否仍为 4？
6. 哪些 solved 题已有 solver 工程化？
7. 哪些 solved 题还只是 artifact / handoff？
8. 现有 local_reverse_constraint_recovery.py 是否已有可复用分发？
9. 是否复用现有 constraint recovery / validation 结构，而不是新建重复 pipeline？
10. 是否避免在 production code 中硬编码真实 candidate？
11. 是否没有运行样本？
12. 是否没有 runtime validation/debugger/hook/emulator/probe？
13. 是否没有修改 training_status/status_overlay？
14. 是否没有读取 full solve_reports？
15. 是否新增或更新了测试？
16. pytest_result 是否包含当前 decision_id/report_id/round_id？
17. artifact_index 是否登记 solver engineering recovery audit artifact？
18. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — solved profile recovery audit

生成：

```text
project_state/local_reverse_solver_engineering_recovery_audit.json
```

内容必须包括：

```text
schema_version
mainline=engineering_branch
round_id=round_20260608_solver_engineering_recovery_foundation_v1
decision_id=decision_20260608_solver_engineering_recovery_foundation_v1
solved_sample_count_before
solved_samples_reviewed
existing_engineered_profiles
missing_engineered_profiles
profile_recovery_candidates
production_hardcode_check
runtime_actions_performed=false
training_status_modified=false
next_recommended_mainline=engineering_branch
next_recommended_action
generated_at
```

至少记录这 4 类：

```text
api_assisted_password_write_and_compare:
  status=existing_initial_solver
  source=local_reverse_constraint_recovery.py

xor_array_table_compare:
  status=missing_solver_profile
  source_sample=cpp1_7b504c54
  evidence=three arrays + reverse index XOR formula

digit_mod_affine_transform_compare:
  status=missing_solver_profile
  source_sample=cpp2_2f64e68d
  evidence=digit domain + modular affine inverse

bytewise_reversible_transform_table_compare:
  status=missing_solver_profile
  source_sample=cpp2_32f1713e
  evidence=target table + self-inverse bit transform
```

### Phase B — minimal solver profile core

优先复用现有 `local_reverse_constraint_recovery.py` 的风格。可以新增：

```text
reverse_agent/local_reverse_solver_profiles.py
```

或在现有文件中增加纯 helper，但必须避免把文件变成单样本脚本。

建议提供这些纯函数能力：

```text
1. invert_xor_array_table(...)
   用于数组 XOR / 倒序索引 / 固定长度表比较。

2. invert_bytewise_transform_table(...)
   用于 0..255 字节域的可逆逐字节变换。
   注意：这是 bounded inverse map，不是 input brute force。

3. invert_digit_mod_affine_table(...)
   用于 digit domain 0..9 的 (a + b*x) % m + offset 逆变换。

4. profile result schema:
   status=SOLVED|PARTIAL|BLOCKED
   candidate
   candidate_generated
   confidence
   proof_chain_summary
   unsupported_reason
```

要求：

```text
- production code 不能包含真实样本路径。
- production code 不能硬编码 KEEP_DREAM / WeKnowItOk / 10013 / hookapi。
- 可以在测试中使用 synthetic fixtures。
- 如果需要引用真实 artifact，只能在 audit artifact 中作为 evidence source，不作为 solver 固定逻辑。
```

### Phase C — tests

新增或扩展测试：

```text
tests/test_local_reverse_solver_profiles.py
```

测试至少覆盖：

```text
1. xor_array_table_compare synthetic case:
   给定 A/B/C 三个数组和 reverse-index XOR 关系，能还原 candidate。

2. bytewise_reversible_transform_table synthetic case:
   给定一个 bit permutation / bit swap transform，能通过 inverse map 还原输入。

3. digit_mod_affine_transform_compare synthetic case:
   给定 digit domain 和 (a + b*x) % 10 + offset，能还原数字字符串。

4. unsupported/non-invertible case:
   多解或无解时返回 PARTIAL/BLOCKED，不猜 candidate。

5. no hardcoded solved candidates:
   production module 中不得出现 KEEP_DREAM / WeKnowItOk / 10013 / hookapi。
```

### Phase D — artifact_index registration

将 audit artifact 注册到：

```text
artifact_index.latest_artifacts["local_reverse_solver_engineering_recovery_audit"]
artifact_index.latest_artifacts_v2["local_reverse_solver_engineering_recovery_audit"]
artifact_index.artifact_refs["local_reverse_solver_engineering_recovery_audit"]
```

`latest_artifacts_v2` 至少包括：

```text
kind=local_reverse_solver_engineering_recovery_audit
path=project_state\\local_reverse_solver_engineering_recovery_audit.json
freshness=current
source_run=round_20260608_solver_engineering_recovery_foundation_v1
sample_id=multi_solved_profile_recovery
mainline=engineering_branch
solved_sample_count_reviewed=4
candidate_generation_performed=false
runtime_validation_attempted=false
training_status_modified=false
```

### Phase E — report

`codex_execution_report.md` 顶部必须包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_solver_engineering_recovery_foundation_v1",
  "round_id": "round_20260608_solver_engineering_recovery_foundation_v1",
  "based_on_decision_id": "decision_20260608_solver_engineering_recovery_foundation_v1",
  "status": "SUCCESS|PARTIAL|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "mainline": "engineering_branch",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

---

## 7. Tests

必须运行：

```bat
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_constraint_recovery.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_solver_profiles.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_solver_profiles.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果没有新建 `local_reverse_solver_profiles.py`，对应 py_compile 命令改为实际被修改的 solver 文件。

`pytest_result.txt` 必须包含：

```text
decision_id=decision_20260608_solver_engineering_recovery_foundation_v1
report_id=report_20260608_solver_engineering_recovery_foundation_v1
round_id=round_20260608_solver_engineering_recovery_foundation_v1
```

---

## 8. Stop Conditions

### ACCEPTED

满足以下条件时可标记为 `SUCCESS / ACCEPTED`：

```text
1. 4 个 solved 样本已完成 solver 工程化差距审计。
2. audit artifact 已生成并注册 current。
3. 至少 3 个 missing profile 已有明确 contract。
4. 至少新增一个纯 solver profile helper 或等价扩展。
5. 新增测试覆盖 XOR array、bytewise reversible transform、digit mod affine 三类 synthetic case。
6. 没有运行样本。
7. 没有 runtime validation/debugger/hook/emulator/probe。
8. 没有修改 training_status/status_overlay。
9. 没有硬编码真实 candidate 到 production code。
10. pytest/lint/git checks 通过。
```

### ACCEPTED_WITH_LIMITATIONS

满足以下条件时可标记为 `PARTIAL / ACCEPTED_WITH_LIMITATIONS`：

```text
1. 完成 solver recovery audit artifact。
2. 明确列出 existing/missing profiles。
3. 只完成部分 profile helper 或测试，但没有违反边界。
4. 给出下一轮具体工程化目标。
```

### REWORK_REQUIRED

出现以下任一情况必须返工：

```text
1. production code 硬编码 KEEP_DREAM / WeKnowItOk / 10013 / hookapi。
2. 运行了本地样本。
3. 做了 runtime validation。
4. 修改了 training_status 或 status_overlay。
5. 重复创建 runtime/debugger/IDA/Ghidra 接口。
6. 没有测试记录。
7. report_id / decision_id / round_id 不匹配。
8. artifact_index 没有登记新 artifact。
```

### BLOCKED

出现以下情况可标记 `BLOCKED`：

```text
1. 必需 solved artifact 缺失。
2. 现有 solver 文件结构冲突，无法安全扩展。
3. project_state lint 失败且不是本轮可修复范围。
```

本轮核心不是“再解一题”，而是把已经解出的 3 个未工程化模式回收到 solver 层。优先级上，先做纯 solver profile 与测试，再考虑接入自动静态提取。

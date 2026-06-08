```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1",
  "round_id": "round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1",
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

本轮主线是 **reverse_solving**。

目标：基于已经 ACCEPTED_WITH_LIMITATIONS 且 cleanup 完成的 `cpp2_883e67b9` 静态公式证据，使用现有 solver/harness/runtime validation 能力生成 candidate，并进行有界验证。若验证成功，写入受控 project_state 解题产物；若验证无法执行或失败，保守记录失败原因，不扩大范围、不回到盲搜。

本轮允许：

```text
1. 从 current project_state artifact 中读取已闭环的公式证据。
2. 根据公式证据生成单一 candidate。
3. 使用现有 solver profile / harness / runtime validation 接口对该 candidate 做有界验证。
4. 将 candidate、验证命令、stdout/stderr 摘要、exit code、成功/失败判定写入新 project_state artifact。
5. 如验证成功，可更新 local reverse training status / status overlay 中 cpp2_883e67b9 的 solved 状态；如项目现有流程要求单独决策才能更新，则只在 artifact 中建议更新，不直接修改。
```

本轮禁止：

```text
1. 不要重新执行 IDA/Ghidra/static extraction。
2. 不要新增 IDA/Ghidra/debugger/runtime/probe 接口。
3. 不要 brute force、dictionary search、beam/topN/budget 扩展。
4. 不要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
5. 不要提交根目录工具 dump。
6. 不要把 candidate、样本路径、本地路径或单样本结论写入 .codex-skills。
7. 不要修改 unrelated solver production code。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`。关键事实：

```text
1. cleanup_lint_report_rework 已解决 lint-report PASSED/FAILED 矛盾。
2. 根目录工具 dump 已删除。
3. 当前静态公式证据仍保存在 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json。
4. artifact_index 中 target_array_xref_boundary_audit 为 freshness=current。
5. 该 artifact 标记 reverse_solving_ready=true。
6. 当前尚未执行 runtime validation，candidate_generated=false，candidate_validation_attempted=false，runtime_validation_attempted=false。
```

可使用的公式证据必须来自 current artifact，而不是记忆或旧 report：

```text
sample_id=cpp2_883e67b9
input_length=15
xor_key_runtime=0x78
target_array_start_va=0x429A34
target_array_length=15
target_array_bytes_hex=33 19 11 32 0D 27 21 11 22 10 11 27 28 3D 36
comparison_formula=input[i] ^ 0x78 == byte_429A34[i] for i in 0..14
inverse_formula=input[i] = byte_429A34[i] ^ 0x78
candidate plaintext is intentionally redacted in tool_integration artifact and must be recomputed in this reverse_solving round.
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复旧 samplereverse 失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

已有工具能力检查要求：在生成或验证 candidate 前，必须检查已有 solver / harness / runtime validation / sample metadata / artifact registration 接口。成熟工具已有的执行、验证、状态登记能力必须复用，不要新写重复框架。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要执行 IDA/Ghidra/static extraction。
2. 不要新增 IDA/Ghidra/debugger/runtime/probe/harness 接口。
3. 不要 brute force、dictionary search、fuzz、beam search、topN search、扩大 timeout/budget。
4. 不要读取完整 solve_reports。
5. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
6. 不要提交根目录工具 dump。
7. 不要把 task_packet.task 当执行权威。
8. 不要把 stale/missing/unknown artifact 当 current。
9. 不要把 candidate 或单样本结论写入 .codex-skills。
10. 不要把本轮变成 engineering refactor 或 tool integration 扩展。
11. 不要修改无关 solver production code。
12. 不要修改 training_status/status_overlay，除非现有流程明确允许 reverse_solving 验证成功后做最小状态同步，并在 report 中列明。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 current 的 cpp2_883e67b9 target_array_xref_boundary_audit artifact。
3. 检查现有 solver profile、harness、runtime validation、sample metadata、artifact registration 接口。
4. 由 current formula evidence 生成单一 candidate。
5. 使用现有 runtime validation/harness 对该 candidate 做一次或少量必要验证。
6. 生成受控 project_state artifact。
7. 更新 artifact_index 登记新 artifact。
8. 更新 codex_execution_report.md 与 pytest_result.txt。
9. 运行 JSON parse、py_compile、pytest、lint、git diff check。
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

必须检查已有能力，避免重复造轮子：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
reverse_agent/local_reverse_runner.py
reverse_agent/local_reverse_training.py
reverse_agent/local_reverse_training_status.py
reverse_agent/harness.py
reverse_agent/sample_metadata.py
tests/test_project_state.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
```

如文件不存在，report 必须说明实际可用的等价接口，不得假设不存在后新建重复框架。

必要时搜索：

```text
runtime_validation
candidate_validation
harness
run_candidate
local_reverse
sample_id
cpp2_883e67b9
artifact_index
solver_profile
status_overlay
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
除 cpp2_883e67b9 current project_state artifact 外的历史重型产物
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 reverse_solving？
3. task_packet 是否仅为 advisory？
4. 是否确认 source artifact freshness=current？
5. 是否确认 sample_id=cpp2_883e67b9、relative_path 与 artifact_index/current_state 一致？
6. 是否检查 negative_results，并说明没有重复 blind search / budget expansion / stale artifact 使用？
7. 是否检查已有 solver/harness/runtime validation/sample metadata/artifact registration 接口？
8. 是否复用已有接口，没有新建重复框架？
9. candidate 是否只由 current formula evidence 计算得到？
10. 是否记录 candidate 生成公式、target bytes、runtime xor key、输入长度？
11. 是否进行了 runtime validation？如果没有，原因是什么？
12. 验证命令、stdin/stdout/stderr 摘要、exit code、timeout、判定依据是什么？
13. 是否没有执行 IDA/Ghidra/static extraction？
14. 是否没有 brute force/dictionary/fuzz/beam/topN/budget 扩展？
15. 是否没有提交根目录工具 dump？
16. 是否没有把 candidate 写入 .codex-skills？
17. 是否生成 project_state/local_reverse_cpp2_883e67b9_candidate_validation.json？
18. artifact_index 是否登记新 artifact，freshness=current、source_run 当前 round、sha256/size_bytes 真实？
19. 如果更新 training_status/status_overlay，是否有验证成功证据和最小变更说明？如果未更新，是否说明原因？
20. 是否运行 JSON parse 校验？
21. 是否运行 py_compile？
22. 是否运行相关 pytest？结果是多少？
23. 是否运行 lint-decision、lint-report、project_state status？
24. 是否运行 git diff --check、git status --short、git diff --name-status？
25. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Evidence and capability check

读取默认 project_state 和 current artifact。确认：

```text
artifact freshness=current
sample identity verified
reverse_solving_ready=true
candidate not already validated
negative_results 不禁止该方向
```

检查已有 solver/harness/runtime validation 接口。若接口不可用，停止生成 runtime claim，只能生成 candidate artifact，并将 validation_status 标记为 `BLOCKED_RUNTIME_INTERFACE_UNAVAILABLE`。

### Phase B — Candidate generation

从 current formula evidence 计算单一 candidate：

```text
candidate[i] = target_array_bytes[i] ^ xor_key_runtime
for i in 0..input_length-1
```

禁止从历史聊天、commit message、旧 report 明文字段或人工记忆复制 candidate。必须在 artifact 中记录计算来源和 provenance。

### Phase C — Candidate validation

优先使用项目现有 runtime validation / harness / runner。验证必须有界：

```text
max_candidates=1
no brute force
no dictionary
no budget expansion
reasonable timeout from existing harness default; 不主动扩大 timeout
stdin 必须只输入 candidate 和必要换行
```

记录：

```text
validation_attempted=true|false
validation_command
stdin_summary
stdout_summary
stderr_summary
exit_code
timeout_seconds
success_indicator
failure_indicator
validation_status=VALIDATED_SUCCESS|VALIDATED_FAILURE|BLOCKED_RUNTIME_INTERFACE_UNAVAILABLE|BLOCKED_SAMPLE_UNAVAILABLE|BLOCKED_SCOPE_WOULD_EXPAND
```

### Phase D — Artifact and status

生成：

```text
project_state/local_reverse_cpp2_883e67b9_candidate_validation.json
```

artifact 必须包含：

```text
schema_version
mainline=reverse_solving
artifact_kind=local_reverse_candidate_validation
sample_id
relative_path
identity_verified
round_id
decision_id
source_artifacts with freshness/source_run
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
candidate_validation_attempted=true|false
runtime_validation_attempted=true|false
training_status_modified=true|false
status_overlay_modified=true|false
```

如果 runtime validation 成功，可最小更新：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
```

但只有在项目已有流程允许且变更极小的情况下执行；否则只在 artifact/report 中建议下一轮状态同步。

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 新 entry：

```text
local_reverse_cpp2_883e67b9_candidate_validation
kind=local_reverse_candidate_validation
path=project_state\local_reverse_cpp2_883e67b9_candidate_validation.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_reverse_solving_candidate_validation_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
candidate_generated=true
candidate_validation_attempted=true|false
runtime_validation_attempted=true|false
validation_status=<status>
sha256=<真实值>
size_bytes=<真实值>
```

---

## 7. Tests

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

If runtime validation is executed through an existing harness, record the exact command and its result in both artifact and report. If runtime validation is blocked, tests still must cover JSON parse/lint/report/status for the generated blocked artifact.

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. source artifact 不是 current，或 sample identity 不匹配。
3. negative_results 禁止当前方向，且没有新增证据理由。
4. 需要重新执行 IDA/Ghidra/static extraction 才能生成 candidate。
5. 需要 brute force/dictionary/fuzz/beam/topN/budget 扩展。
6. 需要新建 runtime/harness/debugger/probe 接口。
7. runtime validation 需要超出已有 harness 默认边界。
8. candidate 不是由 current formula evidence 计算得到。
9. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
10. 新 artifact JSON parse 失败。
11. lint-report/status 无法通过。
12. git diff 包含根目录工具 dump、solve_reports full dump、.codex-skills 动态事实或无关代码变更。
13. 需要修改 training_status/status_overlay 但没有 runtime validation 成功证据。
```

若 candidate 生成成功但 runtime validation 无法执行，允许以 `BLOCKED_RUNTIME_INTERFACE_UNAVAILABLE` 结束，禁止伪造成功。若 validation 失败，记录失败证据并更新 negative_results 建议，不要扩大搜索。
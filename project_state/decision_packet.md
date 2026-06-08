```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
  "round_id": "round_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
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

目标：基于已 ACCEPTED 的 `cpp2_883e67b9_compare_constants_mapping` 及其上游 current artifacts，生成一个有界的 `input length evidence recovery` artifact。该 artifact 只判断当前证据是否支持恢复输入长度、长度上界、终止符或字节域循环线索；不恢复完整校验公式，不生成 candidate，不验证 candidate。

本轮不是 reverse_solving。不要运行样本，不要调用 IDA/Ghidra/debugger/hook/probe/winpty/emulator，不重新读取样本二进制，不扩张静态窗口，不 brute force，不进行 candidate generation / validation。

必须完成：

```text
1. 读取默认 project_state 文件：
   - project_state/task_packet.json
   - project_state/current_state.json
   - project_state/artifact_index.json
   - project_state/negative_results.json
   - project_state/codex_execution_report.md
   - project_state/decision_packet.md
   - project_state/pytest_result.txt

2. 读取并只使用 current 的 cpp2_883e67b9 source artifacts：
   - project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
   - project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json

3. 检查现有 project_state / StructuredEvidence / solver profile / artifact_index / IDA-Ghidra-debugger interface 相关实现，确认本轮复用已有格式，不新建重复接口。

4. 产出新 artifact：
   project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json

5. 新 artifact 必须至少包含：
   - schema_version / mainline / artifact_kind
   - sample_id / relative_path / identity_verified
   - round_id / decision_id
   - source_artifacts 与 source_run / source decision / freshness
   - assert_path_region: 0x5f00-0x6500，focus_assert_path_rva=0x61c3
   - length_related_sites，至少覆盖：
     * 0x64e5 cmp_imm32 0x100
     * 0x6438 cmp_imm8 0xff
     * 0x629f cmp_imm32 0x10c
     * 0x62cb cmp_imm32 0x108
     * 与 loop_0x647d_0x62bb 相关的 branch/loop context
   - per-site record：rva、type、value/value_hex、nearby_loop_cluster、nearby_branch_sites、source_artifacts、length_role_hypothesis、confidence、supports_input_length、blocks_candidate_construction、reasoning
   - allowed length_role_hypothesis：confirmed_input_length | possible_input_length_bound | byte_domain_loop_bound | sentinel_or_mask | table_or_buffer_offset | loop_counter_or_iteration_bound | not_length_evidence | unknown
   - 不允许将任何 site 标为 confirmed_input_length，除非 current source artifact 已有直接证明；当前证据下预计应保持未确认
   - known_input_length / known_input_length_source；若无 current 证据，必须为 null / none
   - input_length_confirmed=false，除非有 current source artifact 支持升级
   - input_length_status: RECOVERED | UNRESOLVED_WITH_HINTS | BLOCKED
   - evidence_gaps_carried_forward：input_length_unknown、no_complete_formula_recovered、known_compare_constant_count_zero、structured_evidence_ready_false
   - recommended_next_mainline：tool_integration，并解释理由
   - candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false

6. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round，并写入真实 sha256 与 size_bytes。

7. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round，并记录 JSON parse 校验。
```

本轮不要求修改 solver 逻辑；除非现有接口无法表达 input_length_evidence_recovery schema，否则不要改 production code。若必须补测试，只允许小范围补充 project_state artifact JSON parse / registration 校验。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮 `compare_constants_mapping_json_rework` 已 ACCEPTED。当前 report/pytest 已绑定：

```text
report_id=report_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
round_id=round_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
decision_id=decision_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
status=SUCCESS / PASSED
```

当前 artifact_index 中 `local_reverse_cpp2_883e67b9_compare_constants_mapping` provenance 已可核验：

```text
path=project_state\local_reverse_cpp2_883e67b9_compare_constants_mapping.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_compare_constants_mapping_json_rework_v1
sha256=eccd63a9ad96b29f0e4ad97826d745617742133c23420825079d9b1ad0b3953a
size_bytes=16824
sample_id=cpp2_883e67b9
constants_mapping_status=MAPPED_WITH_LIMITATIONS
known_compare_constant_count=0
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
next_recommended_mainline=tool_integration
```

Current source evidence summary：

```text
assert_path region: 0x5f00-0x6500
focus_assert_path_rva=0x61c3
known_compare_constant_count=0
formula_recovered=false
candidate_generated=false
runtime_validation_attempted=false
recommended_next_mainline=tool_integration

length-related hints from compare constants mapping:
  0x64e5 cmp_imm32 0x100 -> loop_index_or_bound / medium confidence / pending
  0x6438 cmp_imm8 0xff -> sentinel_or_mask / medium confidence / pending
  0x629f cmp_imm32 0x10c -> table_or_address_constant / low confidence / none
  0x62cb cmp_imm32 0x108 -> table_or_address_constant / low confidence / none

large loop context:
  loop_0x647d_0x62bb contains or neighbors 0x629f, 0x62cb, 0x6438, 0x64e5
```

Current unresolved gaps：

```text
input_length_unknown: blocks candidate_construction
no_complete_formula_recovered: blocks reverse_solving
known_compare_constant_count_zero: blocks solver_profile_normalization
structured_evidence_ready_false: blocks complete_formula_recovery
missing_backward_sites_unresolved: low severity; source-only hints only
```

`task_packet.json` 中旧 samplereverse / queue hint 仍只作建议，不控制本轮。`negative_results.json` 主要约束旧 samplereverse 路线；本轮仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

已有相关能力必须复核但不重复实现：project_state/artifact_index 注册、StructuredEvidence 轻量 schema、solver profile evidence、IDA/Ghidra/debugger interface、字符串 solver。成熟工具已有的反汇编/反编译/调试能力不得在项目内重写。本轮不运行这些工具，只检查已有接口与 current artifacts。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要运行本地样本。
2. 不要执行 candidate generation、candidate validation、negative control、runtime validation。
3. 不要 attach debugger / hook / emulator / probe / winpty。
4. 不要调用 IDA/Ghidra。
5. 不要重新读取样本二进制或扩张静态窗口。
6. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
7. 不要把 cpp2_883e67b9 推进到 candidate 层。
8. 不要把 0x64e5、0x6438 或任何 site 标成 confirmed_input_length，除非 current source artifact 有直接证明。
9. 不要把任何 compare constant 标成 confirmed formula 或 candidate source。
10. 不要修改 local_reverse_training_status.json。
11. 不要修改 training_materials/local_reverse/status_overlay.json。
12. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
13. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
14. 不要重写成熟工具已有的反汇编/反编译能力。
15. 不要读取完整 solve_reports。
16. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
17. 不要提交 full solve_reports。
18. 不要把 task_packet.task 当执行权威。
19. 不要把 stale/missing/unknown artifact 当 current。
20. 不要把本轮变成 reverse_solving、训练状态同步或 runtime validation 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 有界检查相关源码以确认已有接口和避免重复造轮子。
4. 新增 project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json。
5. 更新 artifact_index.json 登记新 artifact，包含真实 sha256/size_bytes。
6. 更新 codex_execution_report.md 和 pytest_result.txt。
7. 执行显式 JSON parse 校验。
8. 如确有必要，补充小范围测试以防 artifact JSON parse / registration regression。
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

project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
```

必须检查已有能力，避免重复造轮子：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
tests/test_project_state.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
```

必要时搜索：

```text
StructuredEvidence
normalized_profile_evidence
profile_evidence
artifact_index
local_reverse_cpp2_883e67b9
input_length
length_role
compare_constants
semantic_role
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
本地样本文件
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 tool_integration？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不生成/验证 candidate？
5. 是否确认没有运行样本、runtime validation、debugger、hook、emulator、probe、winpty？
6. 是否确认没有调用 IDA/Ghidra 或重新读取样本二进制？
7. 是否检查了已有 StructuredEvidence / solver profile / project_state / artifact_index / IDA-Ghidra-debugger 接口？
8. 是否复用了已有接口/格式，而非新建重复框架？
9. 是否读取并只使用 current 的 cpp2_883e67b9 source artifacts？
10. 新 artifact 是否记录 source artifacts/source_run/freshness？
11. 新 artifact 是否覆盖 0x64e5、0x6438、0x629f、0x62cb 及 loop_0x647d_0x62bb context？
12. 新 artifact 是否给出 per-site length_role_hypothesis / confidence / supports_input_length？
13. 新 artifact 是否避免把任何 site 标成 confirmed_input_length，除非有 current source artifact 支持？
14. 新 artifact 是否保持 known_input_length=null/none、input_length_confirmed=false，除非有 current source artifact 支持升级？
15. 新 artifact 是否明确 input_length_status 与 recommended_next_mainline？
16. artifact_index 是否登记新 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值？
17. 是否没有修改 training_status/status_overlay？
18. 是否没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG？
19. 是否没有修改 solver production code？如果修改了，为什么必须修改？
20. 是否运行 JSON parse 校验？
21. 是否运行 py_compile？
22. 是否运行相关 pytest？结果是多少？
23. 是否运行 lint-decision、lint-report、project_state status？
24. 是否运行 git diff --check、git status --short、git diff --name-status？
25. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Inspect current source artifacts only

读取并摘要：

```text
project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
```

只使用 artifact 内已有证据，不重新跑样本、不重新跑 IDA/Ghidra、不扩张静态窗口、不读取本地二进制。

### Phase B — Inspect existing interfaces

有界检查：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_string_solver.py
```

目标是复用已有 schema/字段/注册方式，不新建重复 IDA/Ghidra/debugger/runtime 接口。

### Phase C — Create input length evidence recovery artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
```

建议 schema：

```json
{
  "schema_version": 1,
  "mainline": "tool_integration",
  "artifact_kind": "local_reverse_input_length_evidence_recovery",
  "sample_id": "cpp2_883e67b9",
  "relative_path": "逆向课程2024春02/CPP2.exe",
  "round_id": "round_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
  "decision_id": "decision_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
  "source_artifacts": [],
  "identity_verified": true,
  "assert_path_region": {
    "start_rva": "0x5f00",
    "end_rva_exclusive": "0x6500",
    "focus_assert_path_rva": "0x61c3"
  },
  "length_related_sites": [
    {
      "rva": "0x64e5",
      "type": "cmp_imm32",
      "value": 256,
      "value_hex": "0x100",
      "nearby_loop_cluster": "loop_0x647d_0x62bb",
      "nearby_branch_sites": ["0x647d"],
      "source_artifacts": [],
      "length_role_hypothesis": "byte_domain_loop_bound|possible_input_length_bound|loop_counter_or_iteration_bound|sentinel_or_mask|table_or_buffer_offset|not_length_evidence|unknown",
      "confidence": "low|medium|high",
      "supports_input_length": false,
      "blocks_candidate_construction": true,
      "reasoning": "..."
    }
  ],
  "known_input_length": null,
  "known_input_length_source": "none",
  "input_length_confirmed": false,
  "input_length_status": "UNRESOLVED_WITH_HINTS",
  "formula_recovered": false,
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "recommended_next_mainline": "tool_integration",
  "recommended_next_action": "..."
}
```

若 evidence 不足以确认长度，必须使用 `input_length_status=UNRESOLVED_WITH_HINTS`、`known_input_length=null`、`input_length_confirmed=false`。不要把 0x100 直接当成输入长度；它可能只是 byte-domain loop bound、table size、buffer walk 或 histogram/frequency loop 上界。

### Phase D — Update artifact_index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须加入：

```text
local_reverse_cpp2_883e67b9_input_length_evidence_recovery
```

并在 latest_artifacts、latest_artifacts_v2、artifact_refs 中登记。latest_artifacts_v2 必须包含：

```text
kind=local_reverse_input_length_evidence_recovery
path=project_state\local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=<真实值>
size_bytes=<真实值>
input_length_status=RECOVERED|UNRESOLVED_WITH_HINTS|BLOCKED
input_length_confirmed=false unless directly supported by current source artifacts
known_input_length=null unless directly supported by current source artifacts
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
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增 helper 或 schema test，必须补充对应 pytest 并记录完整命令。

---

## 8. Stop Conditions

立即停止并报告 BLOCKED / REWORK_REQUIRED，如果出现任一情况：

```text
1. decision_packet meta 缺失、不合法，或 active skill profile 不存在。
2. 任一 required source artifact 缺失、stale、unknown，或 sample identity 不匹配。
3. 需要运行样本、runtime validation、debugger、hook、emulator、probe、winpty、IDA/Ghidra 才能完成本轮。
4. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
5. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
6. 需要生成或验证 candidate。
7. 需要扩大静态窗口、预算、枚举空间或重新做二进制分析。
8. 需要新建重复 IDA/Ghidra/debugger/runtime interface。
9. 新 artifact 把任何 site 标为 confirmed_input_length，但没有 current source artifact 支持。
10. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
11. 新 artifact JSON parse 失败。
12. lint-report/status 无法通过。
13. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 `input_length_status=UNRESOLVED_WITH_HINTS`，下一轮仍优先 tool_integration，考虑做 bounded formula-readiness audit 或 current IDA/Ghidra evidence extraction decision；若 `RECOVERED`，下一轮再评估是否进入 reverse_solving。
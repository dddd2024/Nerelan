```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_formula_readiness_audit_v1",
  "round_id": "round_20260608_cpp2_883e67b9_formula_readiness_audit_v1",
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

目标：基于已 ACCEPTED 的 `cpp2_883e67b9_input_length_evidence_recovery` 及其上游 current artifacts，生成一个有界的 `formula readiness audit` artifact。该 artifact 只判断当前静态证据是否足以进入公式恢复 / solver profile normalization / reverse_solving，并明确 focus comparison loops 的已知线索、缺失线索和下一步静态证据需求。

本轮不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本，不调用 IDA/Ghidra/debugger/hook/probe/winpty/emulator，不重新读取样本二进制，不扩张静态窗口，不 brute force，不进行 runtime validation。

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
   - project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
   - project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
   - project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json

3. 检查现有 project_state / StructuredEvidence / solver profile / artifact_index / IDA-Ghidra-debugger interface 相关实现，确认本轮复用已有格式，不新建重复接口。

4. 产出新 artifact：
   project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json

5. 新 artifact 必须至少包含：
   - schema_version / mainline / artifact_kind
   - sample_id / relative_path / identity_verified
   - round_id / decision_id
   - source_artifacts 与 source_run / source decision / freshness
   - assert_path_region: 0x5f00-0x6500，focus_assert_path_rva=0x61c3
   - focus_loops，至少覆盖：
     * loop_0x6081_0x6059
     * loop_0x61e8_0x61b7
     * loop_0x647d_0x62bb 作为 outer/post-compare context
   - per-loop record：loop_id、backward_jump_rva、target_rva、span、nearby_compare_constants、known_branch_sites、known_exit_condition_evidence、known_operand_evidence、known_transform_evidence、missing_evidence、formula_recovery_readiness、confidence、reasoning
   - allowed formula_recovery_readiness：ready_for_formula_recovery | ready_with_limitations | not_ready_static_gaps | blocked_source_artifacts
   - readiness_summary：overall_formula_readiness、known_formula_components、missing_formula_components、solver_profile_normalization_ready、reverse_solving_ready
   - 不允许将 reverse_solving_ready 标为 true，除非 current source artifacts 已直接提供完整公式、输入长度/终止机制和可验证 candidate construction basis；当前证据下预计应为 false
   - 不允许生成 candidate 或把任何 compare constant / loop site 标为 confirmed formula source，除非 current source artifact 有直接证明
   - evidence_gaps_carried_forward：input_length_unknown、no_complete_formula_recovered、known_compare_constant_count_zero、structured_evidence_ready_false、focus_loop_exit_condition_unknown
   - recommended_next_mainline：tool_integration，并解释理由
   - candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false

6. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round，并写入真实 sha256 与 size_bytes。

7. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round，并记录 JSON parse 校验。
```

本轮不要求修改 solver 逻辑；除非现有接口无法表达 formula_readiness_audit schema，否则不要改 production code。若必须补测试，只允许小范围补充 project_state artifact JSON parse / registration 校验。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。`task_packet/current_state` 中旧 samplereverse 候选和 runtime 线索只作为历史状态，不能覆盖当前 cpp2_883e67b9 工具接入主线。

上一轮 `input_length_evidence_recovery` 审计结论为 ACCEPTED_WITH_LIMITATIONS。限制：报告中提到 runtime probe 只能作为远期可能，不得成为本轮默认动作；本轮必须继续静态 / tool_integration 证据补全。

当前 artifact_index 中 `local_reverse_cpp2_883e67b9_input_length_evidence_recovery` provenance 已可核验：

```text
path=project_state\local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1
sha256=b20a864ca3627eff41f2ea215db400ec972da24000ab76955d37f8d6de84634c
size_bytes=14633
sample_id=cpp2_883e67b9
input_length_status=UNRESOLVED_WITH_HINTS
input_length_confirmed=false
known_input_length=null
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
input_length_status=UNRESOLVED_WITH_HINTS
known_input_length=null
input_length_confirmed=false
known_compare_constant_count=0
formula_recovered=false
candidate_generated=false
runtime_validation_attempted=false
recommended_next_mainline=tool_integration

focus comparison loops / contexts:
  loop_0x6081_0x6059: focus comparison loop, exit condition not fully recovered
  loop_0x61e8_0x61b7: focus comparison loop, exit condition not fully recovered
  loop_0x647d_0x62bb: large outer/post-compare loop containing 0x64e5/0x6438/0x629f/0x62cb

length-related conclusions:
  0x64e5 cmp 0x100 -> byte-domain loop bound, not direct input length
  0x6438 cmp 0xff -> sentinel/mask, not direct input length
  0x629f cmp 0x10c and 0x62cb cmp 0x108 -> likely table/buffer offsets, not direct input length
```

Current unresolved gaps：

```text
input_length_unknown: blocks candidate_construction
no_complete_formula_recovered: blocks reverse_solving
known_compare_constant_count_zero: blocks solver_profile_normalization
structured_evidence_ready_false: blocks complete_formula_recovery
focus_loop_exit_condition_unknown: blocks formula reconstruction and implicit length mechanism
missing_backward_sites_unresolved: low severity; source-only hints only
```

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current。

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
8. 不要把任何 focus loop 标为 ready_for_formula_recovery，除非 current source artifact 有直接证明。
9. 不要把 reverse_solving_ready 标为 true，除非 current source artifact 已直接提供完整公式、输入长度/终止机制和 candidate construction basis。
10. 不要把任何 compare constant 标成 confirmed formula 或 candidate source。
11. 不要修改 local_reverse_training_status.json。
12. 不要修改 training_materials/local_reverse/status_overlay.json。
13. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
14. 不要新建重复 IDA/Ghidra/debugger/runtime interface。
15. 不要重写成熟工具已有的反汇编/反编译能力。
16. 不要读取完整 solve_reports。
17. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不要提交 full solve_reports。
19. 不要把 task_packet.task 当执行权威。
20. 不要把 stale/missing/unknown artifact 当 current。
21. 不要把本轮变成 reverse_solving、训练状态同步或 runtime validation 轮。
22. 不要把上一轮提到的 runtime probe 作为本轮执行内容。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 有界检查相关源码以确认已有接口和避免重复造轮子。
4. 新增 project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json。
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

project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
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
formula_readiness
focus_loop
exit_condition
operand_evidence
transform_evidence
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
11. 新 artifact 是否覆盖 loop_0x6081_0x6059、loop_0x61e8_0x61b7、loop_0x647d_0x62bb？
12. 新 artifact 是否给出 per-loop formula_recovery_readiness / known_exit_condition_evidence / missing_evidence？
13. 新 artifact 是否避免把任何 loop 标为 ready_for_formula_recovery，除非有 current source artifact 支持？
14. 新 artifact 是否保持 reverse_solving_ready=false、solver_profile_normalization_ready=false，除非 current source artifact 支持升级？
15. 新 artifact 是否明确 overall_formula_readiness 与 recommended_next_mainline？
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
project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
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

### Phase C — Create formula readiness audit artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
```

建议 schema：

```json
{
  "schema_version": 1,
  "mainline": "tool_integration",
  "artifact_kind": "local_reverse_formula_readiness_audit",
  "sample_id": "cpp2_883e67b9",
  "relative_path": "逆向课程2024春02/CPP2.exe",
  "round_id": "round_20260608_cpp2_883e67b9_formula_readiness_audit_v1",
  "decision_id": "decision_20260608_cpp2_883e67b9_formula_readiness_audit_v1",
  "source_artifacts": [],
  "identity_verified": true,
  "assert_path_region": {
    "start_rva": "0x5f00",
    "end_rva_exclusive": "0x6500",
    "focus_assert_path_rva": "0x61c3"
  },
  "focus_loops": [
    {
      "loop_id": "loop_0x6081_0x6059",
      "backward_jump_rva": "0x6081",
      "target_rva": "0x6059",
      "span": "0x28",
      "nearby_compare_constants": [],
      "known_branch_sites": [],
      "known_exit_condition_evidence": [],
      "known_operand_evidence": [],
      "known_transform_evidence": [],
      "missing_evidence": [],
      "formula_recovery_readiness": "not_ready_static_gaps",
      "confidence": "low|medium|high",
      "reasoning": "..."
    }
  ],
  "readiness_summary": {
    "overall_formula_readiness": "not_ready_static_gaps",
    "known_formula_components": [],
    "missing_formula_components": [],
    "solver_profile_normalization_ready": false,
    "reverse_solving_ready": false
  },
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

若 evidence 不足以确认公式，必须使用 `overall_formula_readiness=not_ready_static_gaps`、`solver_profile_normalization_ready=false`、`reverse_solving_ready=false`。不要把 focus loop 的存在等同于公式恢复完成。

### Phase D — Update artifact_index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须加入：

```text
local_reverse_cpp2_883e67b9_formula_readiness_audit
```

并在 latest_artifacts、latest_artifacts_v2、artifact_refs 中登记。latest_artifacts_v2 必须包含：

```text
kind=local_reverse_formula_readiness_audit
path=project_state\local_reverse_cpp2_883e67b9_formula_readiness_audit.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_formula_readiness_audit_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=<真实值>
size_bytes=<真实值>
overall_formula_readiness=ready_with_limitations|not_ready_static_gaps|blocked_source_artifacts
solver_profile_normalization_ready=false unless directly supported by current source artifacts
reverse_solving_ready=false unless directly supported by current source artifacts
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
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json', encoding='utf-8'))"
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
9. 新 artifact 把 reverse_solving_ready 标为 true，但没有 current source artifact 支持。
10. 新 artifact 把任何 focus loop 标为 ready_for_formula_recovery，但没有 current source artifact 支持。
11. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
12. 新 artifact JSON parse 失败。
13. lint-report/status 无法通过。
14. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 `overall_formula_readiness=not_ready_static_gaps`，下一轮仍优先 tool_integration，考虑生成 current IDA/Ghidra evidence extraction decision 或 focused static re-extraction decision；若 `ready_with_limitations`，下一轮再评估是否进入 reverse_solving。
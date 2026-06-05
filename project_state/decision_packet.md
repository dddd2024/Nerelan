```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_ida_control_flow_recheck_precision_fix_v1",
  "round_id": "round_20260605_cpp1_ida_control_flow_recheck_precision_fix_v1",
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

目标：修复上一轮 `round_20260605_cpp1_bounded_ida_control_flow_recheck_v1` 的 IDA evidence 精度问题。

上一轮不可接受的原因：

```text
1. division / transform / compare 搜索是全局 segment 扫描，不是 _main_0 有界控制流复核。
2. basic_blocks 实际使用 idautils.Chunks，不是真正 basic block。
3. transform/compare 只保存 count，没有保存可审计指令片段。
4. SEH 判断只靠 segment name，结论过强。
5. artifact 给出 SUPPORTED / NOT_PRESENT 等强结论，但证据不足。
```

本轮目标不是求 candidate，而是把 IDA artifact 改成可审计、保守、路径有界的证据产物。

本轮不得动态执行样本，不得做 runtime validation，不得写 candidate / known_candidate，不得标记 solved。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前已有 artifact：

```text
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
```

但该 artifact 只能作为线索，不能作为 accepted current evidence 继续推进，因为其 evidence scope 过宽。

上一轮 artifact 的主要问题：

```text
1. division_instruction_count=12 来自全局 segment 扫描。
2. compare_loop_evidence_count=1352 来自全局 cmp 扫描。
3. transform_loop_evidence_count=61 只保存计数，不保存可审计的局部指令序列。
4. basic_block_count=1 实际是 function chunk，不是真正 basic block。
5. seh_verdict=NOT_PRESENT 依据不足，只能说明 segment-name scan 未发现 SEH。
```

必须保留的状态不变量：

```text
candidate=null
known_candidate=""
runtime_validated=false
executed_sample=false
status=BLOCKED
```

当前可用 current artifacts：

```text
local_reverse_cpp1_2f6fcb63_static_triage: freshness=current
local_reverse_cpp1_2f6fcb63_target_bytes: freshness=current
local_reverse_cpp1_2f6fcb63_inverse_handoff: freshness=current
local_reverse_cpp1_2f6fcb63_transform_recheck: freshness=current
local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck: freshness=current but evidence_precision_rework_required
```

已有工具能力：

```text
1. reverse_agent/tool_runners.py 已提供 IDA executable resolution 能力。
2. reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py 已存在，但 evidence 过宽。
3. tests/test_local_reverse_cpp1_ida_control_flow_recheck.py 已存在，但需要增强 precision 断言。
4. 不允许新建重复通用 IDA runner。
```

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行样本。
2. 不 runtime validation。
3. 不 debugger/runtime probe/hook/emulator。
4. 不运行 old blind solver / brute force。
5. 不扩大 beam、topN、budget、timeout。
6. 不写 candidate。
7. 不写 known_candidate。
8. 不标记 solved。
9. 不修改 local_reverse_training_status.json 为 solved。
10. 不提交 IDA .i64、IDA log、IDB sidecar、原始样本、full solve_reports。
11. 不修改 .codex-skills。
12. 不扩大到其他样本。
13. 不把 task_packet.task 当执行权威。
14. 不新建重复的通用 IDA runner。
15. 不再用全局 segment count 冒充 _main_0 控制流证据。
16. 不把 segment-name scan 未发现 SEH 写成 SEH 不存在的强结论。
```

允许：

```text
1. 修改现有 cpp1 IDA control-flow recheck 脚本。
2. 修改对应测试。
3. 重新运行 bounded headless IDA static extraction。
4. 重新生成 control_flow_recheck artifact。
5. 更新 artifact_index 中该 artifact 的 sha256、size_bytes、modified_at。
6. 更新 codex_execution_report.md 和 pytest_result.txt。
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
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
reverse_agent/tool_runners.py
```

可读取：

```text
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
reverse_agent/local_reverse_cpp1_transform_recheck.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是唯一执行权威。
2. 是否确认 task_packet.task 只是 advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮只修复 IDA evidence precision。
5. 是否改用真正 basic block / FlowChart 或等价控制流结构，而不是 idautils.Chunks。
6. 是否将 division/transform/compare 证据限定到 _main_0 function range / basic blocks。
7. 是否保存 transform loop 的具体指令序列、地址、mnemonic、operands、basic block。
8. 是否保存 compare loop 的具体关键 cmp/jcc 指令，而不是 1352 个全局 cmp count。
9. 是否保存 byte_429A30 xref 与 compare 指令之间的局部上下文。
10. 是否将 SEH verdict 改成保守结论，除非有充分 handler evidence。
11. 是否重新生成 artifact。
12. 是否 artifact 仍为 candidate=null。
13. 是否 artifact 仍为 known_candidate=""。
14. 是否 artifact 仍为 runtime_validated=false。
15. 是否 artifact 仍为 executed_sample=false。
16. 是否没有动态执行样本。
17. 是否没有 runtime validation。
18. 是否没有提交 IDA sidecar/log/raw local temp。
19. 是否 tests_ran 完整。
20. 是否 pytest_result.txt 记录每条命令、Exit Code、输出摘要。
```

---

## 6. Implementation Scope

允许修改：

```text
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_target_byte_extract.py
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
.codex-skills/*
```

实现要求：

```text
1. IDAPython 中使用 ida_gdl.FlowChart 或等价 API 提取 _main_0 basic blocks。
2. 只在 _main_0 function range/basic blocks 内收集 division/transform/compare evidence。
3. transform evidence 必须包含具体 AND/SHL/SHR/OR 指令列表，不能只有 count。
4. compare evidence 必须包含 byte_429A30 xref 附近的局部指令窗口。
5. success/failure branch evidence 必须与具体 jcc/target 地址关联；若无法关联，写 INSUFFICIENT。
6. SEH 证据不足时写 SEH_NOT_CONFIRMED_BY_STATIC_SCAN，不得写 NOT_PRESENT。
7. verdict 必须保守：
   - SUPPORTED 只能在有完整局部指令序列时使用；
   - 否则使用 PARTIALLY_SUPPORTED 或 INSUFFICIENT。
8. artifact 不应提交 .ida_raw.json、.ida_script.py、.i64、.id0、.id1、.nam、.til、.log。
```

`project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json` 至少包含：

```text
schema_version
sample_id
analysis_mode
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
ida_status
main_function
main_function_address
basic_blocks
bounded_instruction_evidence
  - division_instructions_in_main
  - transform_candidate_windows_in_main
  - compare_candidate_windows_in_main
  - target_xref_context
seh_assessment
success_failure_branch_assessment
decompiler_vs_instruction_consistency
control_flow_assessment
candidate=null
known_candidate=""
status=BLOCKED
blocked_reason
recommended_next_action
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_ida_control_flow_recheck --artifact-index project_state/artifact_index.json --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --transform-recheck project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json --triage project_state/local_reverse_cpp1_2f6fcb63_static_triage.json --out project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

Expected results：

```text
1. All required commands Exit Code 0。
2. artifact_index hash/size/modified_at 更新。
3. artifact 只给出与证据强度匹配的保守 verdict。
4. candidate=null，known_candidate=""。
5. runtime_validated=false，executed_sample=false。
6. git diff 只包含允许范围内文件。
7. 无 IDA .i64/log/sidecar/raw temp 文件提交。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 需要动态执行样本才能继续。
2. 需要 runtime validation 才能继续。
3. 需要 debugger/runtime probe/hook/emulator 才能继续。
4. 无法把 evidence 限定到 _main_0。
5. 无法生成真正 basic block/control-flow evidence。
6. artifact 仍只有全局 instruction count。
7. artifact 写入 candidate 或 known_candidate。
8. git status 出现 IDA .i64、IDA log、IDB sidecar、原始样本、full solve_reports 或无关文件。
9. tests 或 lint 失败。
```

完成条件：

```text
1. control_flow_recheck artifact 重新生成并登记 current。
2. evidence 从全局 count 改为 _main_0 局部可审计指令片段。
3. verdict 与证据强度一致，不能过度宣称。
4. 样本仍为 BLOCKED，不写 candidate / known_candidate，不标记 solved。
```
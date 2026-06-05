```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_bounded_ida_control_flow_recheck_v1",
  "round_id": "round_20260605_cpp1_bounded_ida_control_flow_recheck_v1",
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

目标：对 `cpp1_2f6fcb63` 做一次 **有界 IDA 静态控制流 / 指令级 / SEH 复核**，验证当前 decompiler artifact 中的三类关键不确定点：

```text
1. `v6 = v9 / v8` 是否真实位于必经路径，是否受 SEH/异常控制流影响。
2. transform 公式 `(x & 3) | (16 * (x & 0x0C)) | ((x & 0xF0) >> 2)` 是否与指令级证据一致。
3. `strlen==18`、`strncpy(..., 16)`、transform loop、compare loop、`i==16` success condition 的控制流关系是否被 Hex-Rays 误简化。
```

当前 transform recheck 已证明：在当前静态公式和 0x20..0x7e printable ASCII 域下，目标 bytes 不存在完整 printable preimage，artifact 保持 `BLOCKED / NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM`。因此下一步不是 brute force，也不是 runtime validation，而是复核 IDA 指令级和控制流证据。

本轮允许一次有界 headless IDA 静态提取；不允许动态执行样本，不允许 debugger/runtime probe，不允许写 candidate/known_candidate，不允许标记 solved。

预期产物：

```text
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
```

可新增最小工具代码和测试，但必须复用现有 IDA/tool_runners 能力，不得新建重复的通用 IDA runner。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前可用 current artifacts：

```text
local_reverse_cpp1_2f6fcb63_static_triage: freshness=current
local_reverse_cpp1_2f6fcb63_target_bytes: freshness=current
local_reverse_cpp1_2f6fcb63_inverse_handoff: freshness=current
local_reverse_cpp1_2f6fcb63_transform_recheck: freshness=current
```

关键已知事实：

```text
sample_id=cpp1_2f6fcb63
relative_path=逆向课程2023春01/CPP1.exe
source_tool=IDA
target_symbol=byte_429A30
target_address=0x00429A30
target_length=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
main_function=_main_0
main_function_address=0x00401190
executed_sample=false
static_only=true
runtime_validated=false
candidate=null
known_candidate=""
```

`transform_recheck` artifact 当前结论：

```text
mapping_analysis.bijective=true
roundtrip_all_256=true
static_candidate_bytes_hex=5d5a1cde131557d7d69dde2417df2453
static_candidate_printable_ascii=false
all_target_bytes_have_printable_preimage=false
current_static_transform_has_no_printable_solution=true
status=BLOCKED
blocked_reason=NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM
recommended_next_action=bounded IDA instruction-level / control-flow / SEH recheck, not brute force
```

已有工具能力检查：

```text
1. 已有 IDA/tool runner 相关能力：reverse_agent/tool_runners.py、local_reverse_cpp1_target_byte_extract.py、local_reverse_ida_summary.py、local_reverse_forced_ida_extract.py。
2. 已有 IDAPython script 目录与 forced extraction 脚本能力。
3. 已有 cpp1 target byte extraction 脚本和测试。
4. 已有 cpp1 inverse handoff、transform recheck 脚本和测试。
5. 本轮不得新建重复通用 IDA runner；如需新增，只能新增 cpp1 专用、薄包装、复用现有 tool_runners 的 bounded extractor。
6. IDA `.i64`、`.id0`、`.id1`、`.nam`、`.til`、log 均不得作为提交产物。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
```

本轮不触碰 old solver、guided pool、runtime probe 或 full solve_reports。

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行样本。
2. 不做 runtime validation。
3. 不使用 debugger/runtime probe/hook/emulator。
4. 不运行 old blind solver / brute force。
5. 不扩大 beam、topN、budget、timeout。
6. 不写 candidate。
7. 不写 known_candidate。
8. 不标记 solved。
9. 不修改 local_reverse_training_status.json 为 solved。
10. 不提交原始样本、IDA .i64、IDA log、IDB sidecar、full solve_reports 或本地临时目录。
11. 不修改 .codex-skills。
12. 不扩大到其他样本。
13. 不把 task_packet.task 当执行权威。
14. 不新建重复的通用 IDA runner。
15. 不把一次 cpp1 结论写入长期 skill。
```

允许：

```text
1. 读取 current cpp1 artifacts。
2. 复用现有 tool_runners / IDA executable resolution / IDAPython batch 模式。
3. 如现有接口不足，新增 cpp1 专用 bounded IDAPython extractor。
4. 允许一次 bounded headless IDA static extraction，目标限定为 _main_0 / 0x401190 附近控制流、division 指令、transform loop、compare loop、target xrefs、SEH/exception-relevant metadata。
5. 生成一个小型 JSON artifact，登记到 artifact_index。
6. 如果 IDA 不可用，生成 BLOCKED artifact，说明 IDA_UNAVAILABLE，不得伪造证据。
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
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/tool_runners.py
.codex-skills/registry.json
```

可检查：

```text
reverse_agent/ida_scripts/*
tests/test_local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_transform_recheck.py
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
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是 advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮只处理 cpp1_2f6fcb63。
5. 是否检查已有 IDA/tool_runners 能力，避免重复实现通用 runner。
6. 是否确认 static_triage / target_bytes / inverse_handoff / transform_recheck 均为 freshness=current。
7. 是否执行或尝试执行 bounded headless IDA static extraction。
8. 若 IDA 未执行，是否明确记录 IDA_UNAVAILABLE 或前置条件缺失。
9. 是否提取 _main_0 / 0x401190 的 basic blocks、success/failure branches、division 指令上下文、transform loop、compare loop、byte_429A30 xrefs。
10. 是否提取或说明 SEH/exception handling 相关证据是否可获得。
11. 是否对比 decompiler pseudocode 与 instruction-level evidence。
12. 是否明确判断当前 transform formula 是否被指令级证据支持。
13. 是否明确判断 division by zero 是必经 trap、dead code、SEH-mediated path，还是证据不足。
14. 是否明确判断 length/compare semantics 是否支持“前 16 字节决定 success”。
15. 是否生成并登记 control_flow_recheck artifact。
16. 是否保持 candidate=null、known_candidate=""。
17. 是否保持 sample unsolved / BLOCKED 或 NEEDS_STATIC_CONTROL_FLOW_RECHECK。
18. 是否没有动态执行样本。
19. 是否没有 runtime validation。
20. 是否没有恢复或提交 IDA .i64 / IDA log / sidecar。
21. 是否 tests_ran 完整列出 required commands。
22. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
```

---

## 6. Implementation Scope

允许新增：

```text
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
```

如果现有能力不足，允许新增下列最小范围文件：

```text
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
reverse_agent/ida_scripts/cpp1_control_flow_recheck.py
tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改，除非测试暴露确定错误且报告中说明：

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

`local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json` 至少包含：

```text
schema_version
sample_id=cpp1_2f6fcb63
analysis_mode=ida_instruction_control_flow_recheck
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
ida_attempted
ida_available
ida_success
main_function
main_function_address
basic_blocks
success_branch_evidence
failure_branch_evidence
division_instruction_evidence
seh_exception_evidence
transform_loop_instruction_evidence
compare_loop_instruction_evidence
target_xref_evidence
decompiler_vs_instruction_consistency
control_flow_assessment
candidate=null
known_candidate=""
status=BLOCKED 或 NEEDS_STATIC_CONTROL_FLOW_RECHECK 或 IDA_UNAVAILABLE
blocked_reason
recommended_next_action
```

如果 IDA runs successfully, artifact 必须包含 enough evidence snippets to audit conclusions. 如果 IDA unavailable, artifact 必须记录 attempted=false/true、success=false、blocked_reason=IDA_UNAVAILABLE，不得伪造 basic block 证据。

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_ida_control_flow_recheck --artifact-index project_state/artifact_index.json --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --transform-recheck project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json --out project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果 no new wrapper is needed and an existing module is reused, adapt the py_compile/pytest command names to the actual touched files, but the report must explain why no new wrapper was needed.

Expected results：

```text
1. All required commands Exit Code 0，除非 IDA unavailable is intentionally represented by a successful BLOCKED artifact and CLI exit code 0.
2. artifact_index 登记 new control_flow_recheck artifact，freshness=current。
3. artifact candidate=null，known_candidate=""。
4. artifact runtime_validated=false，executed_sample=false。
5. git diff --name-status 只包含本轮允许范围内的新增/修改文件。
6. 不产生 IDA .i64、IDA log、IDB sidecar、solve_reports、原始样本提交。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 需要动态执行样本才能继续。
2. 需要 debugger/runtime probe/hook/emulator 才能继续。
3. 需要写 candidate 或 known_candidate 才能继续。
4. IDA extraction 产生 .i64/log/sidecar 且无法删除或排除提交。
5. artifact_index 无法登记 control_flow_recheck artifact。
6. current source artifacts 缺失或 freshness 非 current。
7. 发现现有 IDA/tool_runners 能力足够但实现重复通用 runner。
8. git status 出现 IDA .i64、IDA log、原始样本、full solve_reports 或无关文件。
```

完成条件：

```text
1. control_flow_recheck artifact 生成并登记 current。
2. 明确说明 division/SEH/control-flow 对当前 blocked 状态的影响。
3. 明确说明 transform formula 是否有 instruction-level 支持。
4. 明确说明 length/compare/success 语义是否支持前 16 字节决定 success。
5. 不标记 solved，不写 candidate，不写 known_candidate。
6. 给出下一轮建议：若 IDA 静态复核仍 blocked，下一轮只能在新 evidence 支撑下决定是否批准 bounded runtime validation；不能回到 brute force 或扩大预算。
```
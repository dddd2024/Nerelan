```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_signed_transform_semantics_recheck_v1",
  "round_id": "round_20260605_cpp1_signed_transform_semantics_recheck_v1",
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

目标：基于 current `_main_0` 局部 IDA evidence，静态复核 `cpp1_2f6fcb63` 的实际 transform 语义，重点处理上一轮留下的三个未决点：

```text
1. 反编译公式中的 `((Destination[i] & 0xF0) >> 2)` 是否应按 IDA 局部指令证据建模为 `movsx` 后的 `sar eax, 2`。
2. `movsx` 对 `Destination[i]` 和 `byte_429A30[i]` 的符号扩展是否影响 inverse/preimage 分析。
3. first-16-byte compare 语义是否足以作为 static preimage analysis 的边界，但仍不能写 candidate/known_candidate 或标记 solved。
```

本轮只做静态 transform/preimage 语义修正，不重新运行 IDA，不动态执行样本，不做 runtime validation，不写 candidate，不写 known_candidate，不标记 solved。

预期产物：

```text
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
tests/test_local_reverse_cpp1_signed_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
```

并将新 artifact 登记进 `project_state/artifact_index.json`，`freshness=current`，`source_run=round_20260605_cpp1_signed_transform_semantics_recheck_v1`。

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 samplereverse advisory，不控制本轮。本轮以本 `project_state/decision_packet.md` 为唯一执行权威。

当前 current artifacts：

```text
local_reverse_cpp1_2f6fcb63_static_triage: freshness=current
local_reverse_cpp1_2f6fcb63_target_bytes: freshness=current
local_reverse_cpp1_2f6fcb63_inverse_handoff: freshness=current
local_reverse_cpp1_2f6fcb63_transform_recheck: freshness=current
local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck: freshness=current
```

上一轮 `control_flow_recheck` 已被审计为 `ACCEPTED_WITH_LIMITATIONS`，可作为 current evidence 使用，但结论必须保守：

```text
main_function=_main_0
main_function_address=0x00401190
basic_block_source=ida_gdl.FlowChart
basic_block_count=16
division_instruction_count=1
transform_candidate_window_count=7
compare_candidate_window_count=11
target_xref_in_main_count=1
transform_formula_verdict=PARTIALLY_SUPPORTED
division_verdict=BOUNDED_MAIN_INSTRUCTION_FOUND
seh_verdict=SEH_NOT_CONFIRMED_BY_STATIC_SCAN
length_compare_semantics_verdict=PARTIALLY_SUPPORTED
status=BLOCKED
candidate=null
known_candidate=""
runtime_validated=false
executed_sample=false
```

关键局部 IDA evidence：

```text
0x0040125C movsx eax, Destination[edx]
0x00401263 and eax, 0F0h
0x00401268 sar eax, 2
0x0040126E movsx edx, Destination[ecx]
0x00401275 and edx, 0Ch
0x00401278 shl edx, 4
0x0040127B or eax, edx
0x00401280 movsx edx, Destination[ecx]
0x00401287 and edx, 3
0x0040128A or eax, edx
0x0040128F mov Destination[ecx], al
```

compare evidence：

```text
0x004012BE movsx ecx, byte_429A30[eax]
0x004012C5 cmp edx, ecx
0x004012C7 jz loc_4012CB
target_xref_related=true
```

success/failure branch association remains conservative：

```text
success_failure_branch_association_count=0
success_failure_branch_assessment.verdict=INSUFFICIENT
```

既有 solver/evidence 能力检查：

```text
1. 已有 `reverse_agent/local_reverse_cpp1_inverse_handoff.py`：旧 unsigned inverse handoff，当前得到不可打印 static candidate。
2. 已有 `reverse_agent/local_reverse_cpp1_transform_recheck.py`：验证旧 forward/inverse bijection 和 printable preimage，但基于旧高层公式。
3. 已有 `reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py`：已产出 current `_main_0` 局部 IDA evidence。
4. 本轮不得重复 IDA runner，不得重新运行 IDA，只读取 current JSON artifacts。
5. 本轮新增的 signed transform recheck 必须是小型 deterministic static analysis，不是 brute force solver，也不是 runtime validation。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
```

本轮不触碰 old sample_solver、guided pool、runtime probe、harness 或 full solve_reports。

---

## 3. Do Not Do

严禁：

```text
1. 不重新运行 IDA。
2. 不动态执行样本。
3. 不做 runtime validation。
4. 不使用 debugger/runtime probe/hook/emulator。
5. 不运行 old blind solver / brute force。
6. 不扩大 beam、topN、budget、timeout。
7. 不写 candidate。
8. 不写 known_candidate。
9. 不标记 solved。
10. 不修改 local_reverse_training_status.json 为 solved。
11. 不提交原始样本、IDA .i64、IDA log、IDB sidecar、raw temp、full solve_reports 或本地临时目录。
12. 不修改 .codex-skills。
13. 不扩大到其他样本。
14. 不把 task_packet.task 当执行权威。
15. 不把一次 cpp1 结论写入长期 skill。
16. 不把 static preimage 当成已验证 flag。
```

允许：

```text
1. 读取 current target_bytes / transform_recheck / inverse_handoff / ida_control_flow_recheck artifacts。
2. 新增 signed transform semantics recheck 脚本和测试。
3. 根据 IDA 局部 evidence 建模 `movsx + and + sar/shl/or + mov al` 的 byte-level transform。
4. 在 0..255 输入域上枚举 forward outputs，比较 unsigned-formula 模型与 signed-instruction 模型。
5. 在 printable ASCII 输入域 0x20..0x7e 上分析每个 target byte 的 preimage 状态。
6. 记录 static preimage options / counts / ambiguity，但保持 `candidate=null`、`known_candidate=""`。
7. 生成 signed_transform_recheck JSON artifact 并登记 artifact_index。
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
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
tests/test_local_reverse_cpp1_transform_recheck.py
tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
.codex-skills/registry.json
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
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认本轮只处理 cpp1_2f6fcb63。
5. 是否确认所有 source artifacts 均为 freshness=current。
6. 是否确认本轮没有重新运行 IDA。
7. 是否确认本轮没有动态执行样本。
8. 是否确认本轮没有 runtime validation。
9. 是否从 current IDA evidence 中读取/确认 `movsx`、`sar`、`shl`、`and`、`or` 指令序列。
10. 是否实现 unsigned high-level formula 与 signed instruction semantics 的对比。
11. 是否明确说明 `sar` 与旧 `shr` 模型在 0..255 上的差异范围。
12. 是否明确说明 `movsx` 是否影响 output byte，尤其是 `mov Destination[ecx], al` 截断后的语义。
13. 是否枚举 printable ASCII 域并给出每个 target byte 的 signed-model preimage 状态。
14. 是否说明 first-16-byte compare 只是 static compare boundary，不等于 runtime validation。
15. 是否保持 candidate=null。
16. 是否保持 known_candidate=""。
17. 是否保持 status=BLOCKED 或 STATIC_PREIMAGE_RECHECKED_NEEDS_VALIDATION，不得 SOLVED。
18. 是否生成 signed_transform_recheck artifact 并登记 artifact_index。
19. 是否 tests_ran 完整列出 required commands。
20. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
21. 是否 git status/diff 没有 IDA sidecar、raw temp、原始样本、solve_reports 或无关文件。
```

---

## 6. Implementation Scope

允许新增：

```text
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
tests/test_local_reverse_cpp1_signed_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改，除非测试暴露确定错误且报告中说明：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json
project_state/local_reverse_cpp1_2f6fcb63_static_triage.json
.codex-skills/*
```

`reverse_agent/local_reverse_cpp1_signed_transform_recheck.py` 至少应提供：

```text
1. u8(x)
2. s8(x)
3. sar32(x, n) or equivalent signed arithmetic shift helper
4. unsigned_formula_transform(x)
5. signed_instruction_transform(x): model movsx, and 0xF0, sar 2, and 0x0C, shl 4, and 3, or, final u8 truncation
6. compare_models_all_256()
7. printable_preimages_for_target(target_bytes, model="signed_instruction")
8. build_signed_transform_report(...)
9. CLI: python -m reverse_agent.local_reverse_cpp1_signed_transform_recheck --target-bytes ... --ida-control-flow ... --transform-recheck ... --out ...
```

`project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json` 至少包含：

```text
schema_version
sample_id=cpp1_2f6fcb63
analysis_mode=signed_instruction_transform_recheck
mainline=reverse_solving
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
ida_instruction_evidence_summary
unsigned_formula_model
signed_instruction_model
model_comparison_all_256
sar_vs_shr_difference_summary
movsx_effect_summary
first_16_compare_boundary
per_byte_printable_preimage_signed_model
static_preimage_status
candidate=null
known_candidate=""
status=BLOCKED 或 STATIC_PREIMAGE_RECHECKED_NEEDS_VALIDATION
blocked_reason
recommended_next_action
```

如果 signed-instruction model yields a complete printable preimage, artifact may record it only under a clearly non-authoritative field such as:

```text
static_preimage_preview_hex
static_preimage_preview_ascii_if_printable
```

但必须保持：

```text
candidate=null
known_candidate=""
runtime_validated=false
status != SOLVED
recommended_next_action=separate bounded validation decision required before accepting candidate
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_signed_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_signed_transform_recheck --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --ida-control-flow project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json --transform-recheck project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json --out project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

Expected results：

```text
1. All required commands Exit Code 0。
2. signed_transform_recheck CLI 生成 JSON artifact。
3. artifact_index 登记新 artifact，freshness=current。
4. artifact candidate=null，known_candidate=""。
5. artifact runtime_validated=false，executed_sample=false。
6. artifact 不标记 solved。
7. git diff --name-status 只包含本轮允许范围内的新增/修改文件。
8. 不产生 IDA .i64、IDA log、raw temp、solve_reports、原始样本提交。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. current target_bytes artifact 缺失或 freshness 非 current。
2. current ida_control_flow_recheck artifact 缺失或 freshness 非 current。
3. current IDA evidence 不含足够 transform instruction snippets，无法安全建模 signed_instruction_transform。
4. 需要重新运行 IDA 才能继续。
5. 需要动态执行样本才能继续。
6. 需要 runtime validation 才能继续。
7. artifact_index 无法登记 signed_transform_recheck artifact。
8. artifact 出现 candidate 非 null。
9. artifact 出现 known_candidate 非空。
10. artifact 出现 runtime_validated=true。
11. artifact 标记 SOLVED。
12. git status 出现 IDA .i64、IDA log、raw temp、原始样本、full solve_reports 或无关文件。
13. tests 或 lint 失败。
```

完成条件：

```text
1. signed_transform_recheck artifact 生成并登记 current。
2. 明确说明 signed-instruction model 与旧 unsigned formula 的差异。
3. 明确说明 sar/movsx 对 printable preimage 的影响。
4. 明确说明 first-16-byte compare 只是静态边界，不是 runtime validation。
5. 样本仍为 BLOCKED 或 STATIC_PREIMAGE_RECHECKED_NEEDS_VALIDATION。
6. candidate=null，known_candidate=""，不标记 solved。
7. 给出下一轮建议：只有在 static evidence 形成单一合理 preimage 且仍保持 unvalidated 时，下一轮才可单独申请 bounded runtime validation；否则继续静态复核，不回到 brute force 或扩大预算。
```
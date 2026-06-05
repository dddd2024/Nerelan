```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_target_byte_provenance_recheck_v1",
  "round_id": "round_20260605_cpp1_target_byte_provenance_recheck_v1",
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

目标：对 `cpp1_2f6fcb63` 做有界的 **target byte provenance recheck**，解释为什么当前 `byte_429A30` 目标字节在已确认 transform 下没有完整 printable preimage，并判断阻断点来自以下哪一类：

```text
1. target bytes / target symbol / target length 提取错误；
2. compare 使用的真实目标常量不是当前 `byte_429A30[0:16]`；
3. transform/compare 前仍存在未建模的静态写入、初始化或数据重定位；
4. 目标字节与 transform 均已被静态确认，但题目接受非 printable 输入或需要额外运行时路径证据。
```

本轮只允许围绕 `cpp1_2f6fcb63` 的 target provenance 做静态/IDA evidence 复核。允许有界运行现有 IDA/IDAPython 静态提取接口或最小扩展现有 `local_reverse_cpp1_target_byte_extract` / `local_reverse_cpp1_ida_control_flow_recheck` 能力，但不得新建重复 IDA runner，不得动态执行样本，不得 runtime validation，不得 brute force candidate。

预期产物：

```text
reverse_agent/local_reverse_cpp1_target_provenance_recheck.py
# 或者对现有 reverse_agent/local_reverse_cpp1_target_byte_extract.py 做最小扩展；二者只能选一条，优先扩展现有能力，避免重复接口。

tests/test_local_reverse_cpp1_target_provenance_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
```

并将新 artifact 登记进 `project_state/artifact_index.json`：

```text
artifact key: local_reverse_cpp1_2f6fcb63_target_provenance_recheck
freshness: current
source_run: round_20260605_cpp1_target_byte_provenance_recheck_v1
sample_id: cpp1_2f6fcb63
```

本轮结束时仍不得写 candidate / known_candidate，不得标记 solved。

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

当前 `project_state/current_state.json` 的 `state_build_id` 仍是：

```text
state_20260602_053948_4e3984041cd7
```

其 digest 为：

```text
4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

`current_state` 的 samplereverse 内容不是本轮主线证据。本轮以 `artifact_index.json`、上一轮 `codex_execution_report.md`、`pytest_result.txt` 和 `cpp1_2f6fcb63` current artifacts 为实际依据。

当前 `artifact_index.json` 已生成于 `2026-06-05T14:12:01Z`。以下 `cpp1_2f6fcb63` artifacts 均为 `freshness=current`：

```text
local_reverse_cpp1_2f6fcb63_static_triage
local_reverse_cpp1_2f6fcb63_target_bytes
local_reverse_cpp1_2f6fcb63_inverse_handoff
local_reverse_cpp1_2f6fcb63_transform_recheck
local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck
local_reverse_cpp1_2f6fcb63_signed_transform_recheck
```

上一轮 `codex_execution_report.md`：

```text
based_on_decision_id=decision_20260605_cpp1_signed_transform_semantics_recheck_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt`：

```text
status=PASSED
12 commands passed
lint-decision OK
lint-report OK
project_state status OK
decision_report_id_match=True
decision_consumed_by_report=True
```

上一轮 signed transform 结论可作为 current evidence 使用：

```text
analysis_mode=signed_instruction_transform_recheck
static_only=true
runtime_validated=false
model_difference_count=0
models_equivalent_after_u8_truncation=true
complete_printable_preimage=false
status=BLOCKED
blocked_reason=NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_SIGNED_MODEL
candidate=null
known_candidate=""
```

关键 transform evidence：

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
0x004012BE movsx ecx, byte_429A30[eax]
0x004012C5 cmp edx, ecx
0x004012C7 jz loc_4012CB
```

当前 target bytes artifact：

```text
source_tool=IDA
target_symbol=byte_429A30
target_address=0x00429A30
target_length=16
target_bytes_hex=d596c4f60745577776e5f64847f74817
expected_target_length=16
```

当前 target / transform 组合产生的问题：

```text
static_candidate_bytes_hex=5d5a1cde131557d7d69dde2417df2453
static_candidate_text=null
printable_ascii=false
NO_PRINTABLE_PREIMAGE_UNDER_CURRENT_STATIC_TRANSFORM
```

已知 printable preimage 缺失位置来自 `transform_recheck`：

```text
index 0  target d5 => printable preimage ']'
index 1  target 96 => printable preimage 'Z'
index 2  target c4 => no printable preimage
index 3  target f6 => no printable preimage
index 4  target 07 => no printable preimage
index 5  target 45 => no printable preimage
index 6  target 57 => printable preimage 'W'
index 7  target 77 => no printable preimage
index 8  target 76 => no printable preimage
index 9  target e5 => no printable preimage
index 10 target f6 => no printable preimage
index 11 target 48 => printable preimage '$'
index 12 target 47 => no printable preimage
index 13 target f7 => no printable preimage
index 14 target 48 => printable preimage '$'
index 15 target 17 => printable preimage 'S'
```

当前 `local_reverse_training_status.json` 对 `cpp1_2f6fcb63` 仍显示 `inventory_only`，与 artifact_index 中已有多轮 current artifacts 不一致。本轮不得顺手重写 training status；仅可在报告里记录该状态文件是低优先级/可能 stale 的训练集摘要，不得把它当作本轮状态权威。

已有相关能力检查：

```text
1. 已有 IDA 静态输出与 Hex-Rays evidence；不得假设 IDA/Ghidra/debugger 不存在。
2. 已有 reverse_agent/local_reverse_cpp1_target_byte_extract.py。
3. 已有 reverse_agent/local_reverse_cpp1_inverse_handoff.py。
4. 已有 reverse_agent/local_reverse_cpp1_transform_recheck.py。
5. 已有 reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py。
6. 已有 reverse_agent/local_reverse_cpp1_signed_transform_recheck.py。
7. 本轮应复用或最小扩展上述能力，不得新建重复 IDA runner。
```

当前 negative_results 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
6. run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰 samplereverse runtime probe、guided pool、old solver、full solve_reports 或 candidate search。

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
10. 不把 non-printable static inverse 当 flag。
11. 不提交原始样本、IDA .i64、IDA log、IDB sidecar、raw temp、full solve_reports 或本地临时目录。
12. 不修改 .codex-skills。
13. 不扩大到其他样本。
14. 不把 task_packet.task 当执行权威。
15. 不把一次 cpp1 结论写入长期 skill。
16. 不复制/新建第二套 IDA runner；成熟工具接口和现有脚本优先。
17. 不用 `local_reverse_training_status.json` 的 inventory_only 覆盖 artifact_index 的 current evidence。
```

允许：

```text
1. 读取 current `cpp1_2f6fcb63` artifacts。
2. 读取现有 cpp1 静态分析脚本和测试。
3. 有界运行现有 IDA/IDAPython 静态提取入口，前提是只针对 `cpp1_2f6fcb63`，且输出轻量 JSON artifact。
4. 最小扩展 `local_reverse_cpp1_target_byte_extract.py` 或 `local_reverse_cpp1_ida_control_flow_recheck.py`，补充 target symbol/raw data/xref/section/provenance 字段。
5. 如确需新增 `local_reverse_cpp1_target_provenance_recheck.py`，必须解释为什么不能直接扩展现有脚本，并保证不重复 IDA runner。
6. 枚举 `byte_429A30` 附近小窗口候选 target spans，例如 ±0x40 bytes 内的 16/18-byte slices，并只做 static printable-preimage feasibility analysis，不输出 candidate。
7. 记录 compare xref、data xref、section、raw bytes window、symbol span、target length、signed compare interpretation 和 provenance verdict。
8. 生成 target_provenance_recheck JSON 并登记 artifact_index。
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
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
tests/test_local_reverse_cpp1_target_byte_extract.py
tests/test_local_reverse_cpp1_transform_recheck.py
tests/test_local_reverse_cpp1_ida_control_flow_recheck.py
tests/test_local_reverse_cpp1_signed_transform_recheck.py
.codex-skills/registry.json
```

按需读取：

```text
project_state/local_reverse_training_status.json
project_state/local_reverse_inventory.json
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认本轮只处理 cpp1_2f6fcb63。
5. 是否确认 source artifacts 均来自 artifact_index 且 freshness=current。
6. 是否确认上一轮 signed_transform_recheck 已被 SUCCESS report 消费，且 pytest_result 12 条命令通过。
7. 是否确认 signed/unsigned transform 在 u8 输出上全域等价。
8. 是否确认当前 target bytes 与 transform 组合没有完整 printable preimage。
9. 是否说明本轮是否运行了 IDA；如果运行，必须说明是 bounded static extraction，不是动态执行。
10. 是否说明使用的是现有 IDA/IDAPython 接口或对现有脚本的最小扩展，未重复造 runner。
11. 是否输出 `byte_429A30` 的 section、symbol span、raw data window 和 compare/data xrefs。
12. 是否证明当前 `target_bytes_hex=d596c4f60745577776e5f64847f74817` 与 IDA/raw data 一致，或给出不一致原因。
13. 是否检查 `byte_429A30` 周围小窗口 16/18-byte candidate spans 的 printable-preimage feasibility。
14. 是否明确区分：target provenance confirmed / target provenance inconsistent / insufficient evidence。
15. 是否明确说明 `movsx byte_429A30[eax]` 下 bytes >0x7f 只是 signed compare 值，不自动说明 target 提取错误。
16. 是否没有写 candidate。
17. 是否没有写 known_candidate。
18. 是否没有 runtime_validated=true。
19. 是否没有标记 solved。
20. 是否生成 `project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json`。
21. 是否将 artifact 登记到 `project_state/artifact_index.json`，freshness=current，source_run=round_20260605_cpp1_target_byte_provenance_recheck_v1。
22. 是否 tests_ran 完整列出 required commands。
23. 是否 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
24. 是否 git status/diff 没有 IDA sidecar、raw temp、原始样本、solve_reports 或无关文件。
```

---

## 6. Implementation Scope

优先方案：最小扩展现有 target extraction / control-flow recheck 能力，避免重复 IDA runner。

允许新增：

```text
reverse_agent/local_reverse_cpp1_target_provenance_recheck.py
# 仅当无法合理扩展现有脚本时新增。

tests/test_local_reverse_cpp1_target_provenance_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
```

允许修改：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_cpp1_ida_control_flow_recheck.py
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改，除非测试暴露确定错误且报告中说明：

```text
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
project_state/local_reverse_cpp1_2f6fcb63_inverse_handoff.json
project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json
project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json
project_state/local_reverse_training_status.json
.codex-skills/*
```

`project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json` 至少包含：

```text
schema_version
sample_id=cpp1_2f6fcb63
analysis_mode=target_byte_provenance_recheck
mainline=reverse_solving
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
source_artifact_freshness
ida_used_this_round: true/false
ida_invocation_scope: none | bounded_static_target_provenance_only
used_existing_ida_interface: true
new_ida_runner_created: false
target_symbol=byte_429A30
target_address=0x00429A30
target_length_candidates
confirmed_target_bytes_hex
raw_data_window
section_name
symbol_span
compare_xrefs
data_xrefs
nearby_candidate_spans
printable_preimage_feasibility_by_span
signed_compare_notes
provenance_verdict: CONFIRMED_NO_PRINTABLE_PREIMAGE | INCONSISTENT_TARGET_BYTES | INSUFFICIENT_TARGET_PROVENANCE | ALTERNATIVE_PRINTABLE_SPAN_FOUND_NEEDS_REVIEW
candidate=null
known_candidate=""
status=BLOCKED
blocked_reason
recommended_next_action
```

`nearby_candidate_spans` 必须是 bounded：

```text
1. 只允许检查 `byte_429A30` 周围最多 ±0x40 bytes。
2. 只允许 16-byte 和 18-byte span feasibility。
3. 不允许把任何 span 直接输出为 candidate。
4. 如果发现完整 printable preimage span，只能记录为 `alternative_static_span_needs_review`，不得标记 solved。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_target_provenance_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_target_provenance_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_target_byte_extract.py
python -m pytest -q tests/test_local_reverse_cpp1_transform_recheck.py
python -m pytest -q tests/test_local_reverse_cpp1_signed_transform_recheck.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.local_reverse_cpp1_target_provenance_recheck --target-bytes project_state/local_reverse_cpp1_2f6fcb63_target_bytes.json --transform-recheck project_state/local_reverse_cpp1_2f6fcb63_transform_recheck.json --signed-transform-recheck project_state/local_reverse_cpp1_2f6fcb63_signed_transform_recheck.json --ida-control-flow project_state/local_reverse_cpp1_2f6fcb63_ida_control_flow_recheck.json --out project_state/local_reverse_cpp1_2f6fcb63_target_provenance_recheck.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果 Codex 选择不新增 `reverse_agent/local_reverse_cpp1_target_provenance_recheck.py`，而是扩展现有 `local_reverse_cpp1_target_byte_extract.py`，则必须将第一、第二、第七条命令替换为对应现有模块/测试命令，并在报告中解释替换原因。

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. 当前 required source artifact 缺失或 artifact_index 中 freshness 不是 current。
2. 发现 decision_packet 与 codex_execution_report round/decision 不匹配，且无法先修复状态。
3. 现有 IDA 接口不可用，且无法只用 current artifacts 完成 target provenance recheck。
4. 需要动态执行样本才能判断 target provenance。
5. 需要 debugger/runtime probe/hook/emulator。
6. 需要读取 full solve_reports 或 PROJECT_PROGRESS_LOG 才能继续。
7. 需要提交原始样本、IDA sidecar、raw temp 或 full solve_reports。
8. 发现 target provenance 与当前 artifact 冲突，但无法给出 bounded 修复方案。
```

成功完成的最低标准：

```text
1. 生成 target_provenance_recheck artifact。
2. 明确给出 provenance_verdict。
3. 明确说明当前 target bytes 是否被确认。
4. 明确说明是否存在 nearby printable alternative span。
5. 保持 candidate=null、known_candidate=""、runtime_validated=false。
6. artifact_index 登记 current artifact。
7. tests 和 project_state lint/status 记录完整。
```

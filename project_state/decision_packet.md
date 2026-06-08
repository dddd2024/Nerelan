```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_target_array_xref_boundary_audit_v1",
  "round_id": "round_20260608_cpp2_883e67b9_target_array_xref_boundary_audit_v1",
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

目标：基于已 ACCEPTED_WITH_LIMITATIONS 的 `cpp2_883e67b9_ida_ghidra_focus_loop_extraction`，继续使用已有成熟工具接口，对 `byte_429A34` 目标数组做有界静态 XREF、边界、数据段偏移和公式证据审计。重点是确认：

```text
1. byte_429A34 的真实数组起点、长度和连续字节值；
2. 所有对 byte_429A34 / byte_429A30 / byte_429A31 / Str 的静态 XREF；
3. sub_4011E0 中是否只有 Str[i] ^= 0x66 后与 byte_429A34[i] 比较，还是存在额外变换、索引偏移、类型符号扩展或前置初始化；
4. byte_429A34[i] ^ 0x66 解码不清晰 ASCII 的原因是数组偏移错误、边界错误、编码/宽字符问题、额外 transform，还是目标确实为非典型可打印串；
5. 是否可以形成不生成 candidate 的公式证据摘要，为下一轮 reverse_solving 决策做准备。
```

本轮仍不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本交互逻辑，不 attach debugger/hook/probe/winpty/emulator，不 brute force，不做 runtime validation。允许的工具行为仅限 **已有接口驱动的 IDA/Ghidra/headless 静态分析或同等静态提取**。IDA/Ghidra 能完成的反汇编、XREF、伪代码和数据段提取，不要在项目中重写。

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
   - project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json
   - project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
   - project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
   - project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
   - project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json

3. 检查已有 IDA / IDAPython / Ghidra / static extraction / StructuredEvidence 接口，复用已有接口，不新建重复框架。

4. 若现有 IDA 静态接口可用，执行有界静态提取或复用当前 IDA 输出，只覆盖：
   - sample_id=cpp2_883e67b9
   - functions: sub_401090, sub_4011E0, direct thunk/caller functions sub_401005, sub_40100A, _main_0
   - data symbols: byte_429A30, byte_429A31, byte_429A34, Str
   - data window: 0x429A20-0x429A60, unless current IDA XREF proves a smaller/larger precise range is required
   - XREFs to byte_429A34 / byte_429A30 / byte_429A31 / Str

5. 产出新 artifact：
   project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json

6. 新 artifact 必须至少包含：
   - schema_version / mainline / artifact_kind
   - sample_id / relative_path / identity_verified
   - round_id / decision_id
   - source_artifacts 与 source_run / source decision / freshness
   - tool_capability_check：IDA/Ghidra/static extraction 是否可用、是否执行、命令摘要、输出来源、退出码或失败原因
   - target_symbols：byte_429A30、byte_429A31、byte_429A34、Str 的 VA/RVA/file_offset/size/value/source
   - byte_429A34_boundary_candidates：至少比较 0x429A32、0x429A34、0x429A36 等合理邻近起点，记录每个起点的 15 字节切片、xor_0x66_preview、printability_score、reason_not_selected/selected_reason
   - selected_target_array_boundary：start_va、file_offset、length、bytes_hex、xor_key、decoded_preview、selection_confidence
   - xrefs：对 byte_429A34 / byte_429A30 / byte_429A31 / Str 的静态 XREF 列表，包含 from_function、instruction/statement、access_type、index_expression
   - transform_chain_hypothesis：仅从 current static tool output 推导，禁止猜测；记录是否存在额外 transform、索引偏移、wide-char/encoding 线索、sign/zero extension 线索
   - formula_evidence_summary：input_length、xor_key、target_array、comparison_formula、remaining_ambiguities
   - structured_evidence_projection_update：若可转换，生成轻量 StructuredEvidence update；若不可转换，记录原因
   - readiness_update：formula_boundary_resolved、target_array_boundary_confidence、solver_profile_normalization_ready、reverse_solving_ready、recommended_next_mainline
   - candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false

7. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round，并写入真实 sha256 与 size_bytes。

8. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round，并记录 JSON parse 校验。
```

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。

上一轮审计结论：`cpp2_883e67b9_ida_ghidra_focus_loop_extraction` 为 ACCEPTED_WITH_LIMITATIONS。核心进展：

```text
extraction_status=SUCCESS_STATIC_EVIDENCE_EXTRACTED
selected_static_extraction_path=ida
reverse_solving_ready=false
candidate_generated=false
candidate_validation_attempted=false
runtime_validation_attempted=false
training_status_modified=false
status_overlay_modified=false
```

IDA/Hex-Rays 已提取到的当前证据：

```text
sub_401090:
  scanf("%s", Str)
  strlen(Str) == byte_429A31
  byte_429A31 = 0x0f = 15

sub_4011E0:
  for i in range(byte_429A31):
    Str[i] ^= byte_429A30
    if Str[i] != byte_429A34[i]: fail
  success otherwise

known data:
  byte_429A30 = 0x66
  byte_429A31 = 0x0f
  byte_429A34 = target comparison array, reported length 15
```

仍未闭环的限制：

```text
1. byte_429A34[i] ^ 0x66 未得到清晰 printable ASCII。
2. 可能存在目标数组起点/边界偏移错误。
3. 可能存在额外 transform、编码、索引或符号扩展问题。
4. loop_0x647d_0x62bb 未被证明属于 password check，上一轮保守认为可能非核心逻辑。
5. 尚未进行 runtime validation，也不应在本轮进行。
```

本轮不能把上述证据直接升级为 candidate。只能把工具输出结构化成更精确的公式/边界证据。

`negative_results.json` 仍必须遵守：不回到 blind search，不扩大预算，不提交 full solve_reports，不把 stale/missing artifact 当 current，不重复旧 samplereverse 失败方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving。
2. 不要生成 candidate、验证 candidate、运行 negative control 或 runtime validation。
3. 不要运行样本交互逻辑。
4. 不要 attach debugger / hook / emulator / probe / winpty。
5. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
6. 不要回到 old sample_solver blind search。
7. 不要把 cpp2_883e67b9 推进到 candidate 层。
8. 不要把 byte_429A34 的任意边界标为 confirmed，除非 current IDA/Ghidra/static tool output 或可复核数据切片直接支持。
9. 不要把 reverse_solving_ready 标为 true，除非 current static evidence 已直接提供完整公式、输入长度、目标数组边界和 candidate construction basis；即使为 true，本轮也不要生成 candidate。
10. 不要修改 local_reverse_training_status.json。
11. 不要修改 training_materials/local_reverse/status_overlay.json。
12. 不要把本地路径、candidate、单样本结论写入 .codex-skills。
13. 不要新建重复 IDA/Ghidra/debugger/runtime interface；必须先复用或审计已有接口。
14. 不要重写成熟工具已有的反汇编/反编译能力。
15. 不要读取完整 solve_reports。
16. 不要读取完整 PROJECT_PROGRESS_LOG.txt。
17. 不要提交 full solve_reports。
18. 不要把 task_packet.task 当执行权威。
19. 不要把 stale/missing/unknown artifact 当 current。
20. 不要把本轮变成训练状态同步或 runtime probe 轮。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取与 cpp2_883e67b9 直接相关的 current project_state artifacts。
3. 有界检查相关源码以确认已有 IDA/Ghidra/static extraction/StructuredEvidence 接口。
4. 使用已有 IDA/Ghidra/static extraction 接口提取 byte_429A34/byte_429A30/byte_429A31/Str 的静态 XREF 与数据边界。
5. 有界读取样本二进制的 data window 字节，仅用于验证 current IDA data symbol 的 file_offset/bytes；必须记录范围和理由。
6. 新增 project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json。
7. 更新 artifact_index.json 登记新 artifact，包含真实 sha256/size_bytes。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
9. 执行显式 JSON parse 校验。
10. 如确有必要，补充小范围 project_state artifact registration 或 JSON parse 测试。
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

project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json
project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
```

必须检查已有能力，避免重复造轮子：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_string_solver.py
tests/test_project_state.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
```

必要时搜索：

```text
byte_429A34
byte_429A30
byte_429A31
Str
IDA
IDAPython
collect_evidence
StructuredEvidence
artifact_index
target_array
xref
formula_readiness
```

不要默认读取：

```text
solve_reports/ full tree
PROJECT_PROGRESS_LOG.txt full file
project_state/rounds/ full history
除 cpp2_883e67b9 当前 artifact 外的历史重型产物
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. decision_packet 是否是唯一执行权威？
2. mainline 是否为 tool_integration？
3. task_packet 是否仅为 advisory？
4. 是否确认本轮不是 reverse_solving，不生成/验证 candidate？
5. 是否确认没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty？
6. 是否读取并只使用 current 的 cpp2_883e67b9 source artifacts？
7. 是否检查并复用了已有 IDA / IDAPython / static extraction / StructuredEvidence 接口？
8. 是否没有新建重复工具接口或手写替代反汇编器？
9. 是否记录 byte_429A34 / byte_429A30 / byte_429A31 / Str 的 XREF、VA/RVA/file_offset、访问方式？
10. 是否给出 byte_429A34 边界候选对比和 selected_target_array_boundary？
11. 是否解释 byte_429A34[i] ^ 0x66 不清晰 ASCII 的原因或仍然无法解释的证据缺口？
12. 是否明确是否存在额外 transform、索引偏移、wide-char/encoding、sign/zero extension 线索？
13. 是否保持 candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false？
14. 是否没有修改 training_status/status_overlay？
15. artifact_index 是否登记新 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值？
16. 是否运行 JSON parse 校验？
17. 是否运行 py_compile？
18. 是否运行相关 pytest？结果是多少？
19. 是否运行 lint-decision、lint-report、project_state status？
20. 是否运行 git diff --check、git status --short、git diff --name-status？
21. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Inspect current evidence only

读取并摘要 current source artifacts，重点是上一轮 IDA artifact 中：

```text
sub_401090
sub_4011E0
byte_429A30
byte_429A31
byte_429A34
Str
formula_readiness_update
structured_evidence_projection.reason
missing_evidence_after_extraction
```

### Phase B — Interface and data-source check

确认是否复用：

```text
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/local_reverse_ida_guided_solver.py
```

如果需要执行 IDA，必须记录完整命令、环境变量、focus functions/data symbols、输出路径、退出码。若不执行 IDA而复用上一轮 artifact，必须说明复用理由和当前 freshness。

### Phase C — Target array boundary and XREF audit

生成 `target_array_boundary_candidates`，至少覆盖：

```text
candidate_start_va=0x429A32, length=15, xor_key=0x66
candidate_start_va=0x429A34, length=15, xor_key=0x66
candidate_start_va=0x429A36, length=15, xor_key=0x66
```

每个候选必须记录：

```text
bytes_hex
xor_0x66_hex
xor_0x66_ascii_preview
printable_count
printability_score
selection_status: selected | rejected | inconclusive
selection_reason
```

XREF 审计必须覆盖：

```text
byte_429A34 read sites
byte_429A30 read sites
byte_429A31 read sites
Str read/write sites
sub_4011E0 comparison instruction/pseudocode
sub_401090 length check instruction/pseudocode
```

### Phase D — Create artifact

生成：

```text
project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
```

允许状态：

```text
SUCCESS_BOUNDARY_RESOLVED
PARTIAL_BOUNDARY_AMBIGUOUS
BLOCKED_TOOL_UNAVAILABLE
BLOCKED_XREF_INSUFFICIENT
BLOCKED_SCOPE_WOULD_EXPAND
```

如果 `PARTIAL_BOUNDARY_AMBIGUOUS`，必须列出下一步最小静态证据缺口，不要转向 runtime validation。

### Phase E — Update artifact_index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须加入：

```text
local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit
```

latest_artifacts_v2 entry 必须包含：

```text
kind=local_reverse_target_array_xref_boundary_audit
path=project_state\local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_target_array_xref_boundary_audit_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=<真实值>
size_bytes=<真实值>
boundary_audit_status=SUCCESS_BOUNDARY_RESOLVED|PARTIAL_BOUNDARY_AMBIGUOUS|BLOCKED_TOOL_UNAVAILABLE|BLOCKED_XREF_INSUFFICIENT|BLOCKED_SCOPE_WOULD_EXPAND
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
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py
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
3. 需要运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty 才能完成本轮。
4. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
5. 需要修改 local_reverse_training_status.json 或 status_overlay.json。
6. 需要生成或验证 candidate。
7. 需要扩大静态窗口、预算、枚举空间或重新做无界二进制分析。
8. 需要新建重复 IDA/Ghidra/debugger/runtime interface 才能继续。
9. 现有 IDA/Ghidra/static interface 不可用，但 report 仍声称提取成功。
10. 新 artifact 把 reverse_solving_ready 标为 true，但没有 current static evidence 直接支持完整公式和 target array boundary。
11. 新 artifact 把 target array boundary 标为 confirmed，但没有 current XREF/data evidence 支持。
12. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
13. 新 artifact JSON parse 失败。
14. lint-report/status 无法通过。
15. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 `SUCCESS_BOUNDARY_RESOLVED` 且公式证据完整，下一轮再评估是否切换到 `reverse_solving`；若 `PARTIAL_BOUNDARY_AMBIGUOUS`，下一轮继续 tool_integration，先补最小静态证据缺口。
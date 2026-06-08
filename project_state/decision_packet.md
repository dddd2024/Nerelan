```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260608_cpp2_883e67b9_ida_ghidra_focus_loop_extraction_v1",
  "round_id": "round_20260608_cpp2_883e67b9_ida_ghidra_focus_loop_extraction_v1",
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

目标：基于已 ACCEPTED 的 `cpp2_883e67b9_formula_readiness_audit`，先复核仓库中现有 IDA/Ghidra/静态提取接口，再用已有成熟工具接口对 `cpp2_883e67b9` 的 focus loops 做有界静态证据提取或工具可用性审计。目标是补齐真实反汇编、伪代码/函数边界、XREF、branch target、operand/data role、loop exit condition 和 transform evidence，不进入解题。

本轮不是 reverse_solving。不要生成 candidate，不要验证 candidate，不运行样本交互逻辑，不 attach debugger/hook/probe/winpty/emulator，不 brute force，不做 runtime validation。允许的工具行为仅限 **已有接口驱动的 IDA/Ghidra/headless 静态分析或同等静态提取**；如果现有接口不可用或配置缺失，必须记录 `BLOCKED_TOOL_UNAVAILABLE`，不要新建重复接口，不要手写替代反汇编器。

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
   - project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
   - project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
   - project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
   - project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
   - project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
   - project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
   - project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json

3. 必须先检查现有工具接口，避免重复造轮子：
   - IDA / IDAPython runner 或脚本
   - Ghidra headless runner 或脚本
   - objdump/radare2/file/strings 静态接口
   - StructuredEvidence 转换接口
   - project_state/artifact_index 注册接口
   - solver profile evidence 接口
   - 任何已有 debugger/runtime/probe 接口只允许记录存在性，不允许执行

4. 若已有 IDA/Ghidra 静态接口可用，执行有界静态提取，仅覆盖：
   - sample_id=cpp2_883e67b9
   - focus range 0x5f00-0x6500
   - focus loops:
     * loop_0x6081_0x6059
     * loop_0x61e8_0x61b7
     * loop_0x647d_0x62bb
   - focus RVAs:
     * 0x6059, 0x6077, 0x6081, 0x60a3, 0x60b5
     * 0x61b7, 0x61bd, 0x61de, 0x61e8, 0x61f0
     * 0x6290, 0x6294, 0x629f, 0x62a7, 0x62b2, 0x62cb, 0x6438, 0x645f, 0x647d, 0x64b2, 0x64e5

5. 产出新 artifact：
   project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json

6. 新 artifact 必须至少包含：
   - schema_version / mainline / artifact_kind
   - sample_id / relative_path / identity_verified
   - round_id / decision_id
   - tool_capability_check：现有 IDA/Ghidra/objdump/radare2/strings/StructuredEvidence 接口是否存在、是否可用、是否执行、执行命令摘要、失败原因
   - source_artifacts 与 source_run / source decision / freshness
   - extracted_focus_ranges / focus_rvas
   - per-loop extraction：loop_id、function_name/function_start、basic_blocks、instructions、branch_targets、xref_in/out、decompiler_pseudocode_if_available、operands、stack_vars/registers、calls_inside_loop、constants_inside_loop、exit_condition_hypothesis、data_role_hypothesis、confidence、evidence_source
   - structured_evidence_projection：若可转换，生成轻量 StructuredEvidence；若不可转换，记录 reason
   - formula_readiness_update：overall_formula_readiness、solver_profile_normalization_ready、reverse_solving_ready、missing_evidence_after_extraction
   - 不允许把 reverse_solving_ready 标为 true，除非提取结果直接提供完整公式、输入长度/终止机制和可验证 candidate construction basis
   - 不允许生成 candidate 或把任何 loop/constant 标成 confirmed formula source，除非工具输出直接证明
   - candidate_generated=false、candidate_validation_attempted=false、runtime_validation_attempted=false、training_status_modified=false、status_overlay_modified=false

7. 若工具不可用或现有接口缺失，仍产出同一路径 artifact，但状态必须为 BLOCKED_TOOL_UNAVAILABLE，并列出：
   - checked_interfaces
   - missing_or_unconfigured_tools
   - nearest_existing_interface
   - recommended_next_action
   - no_tool_execution_performed=true

8. 更新 project_state/artifact_index.json，将新 artifact 登记到 latest_artifacts、latest_artifacts_v2、artifact_refs，freshness=current，source_run 为本轮 round，并写入真实 sha256 与 size_bytes。

9. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，绑定当前 decision/report/round，并记录 JSON parse 校验。
```

本轮原则：成熟工具优先。IDA/Ghidra 能完成的反汇编、函数边界、XREF、伪代码和基本块提取，不要在项目中重写。reverse-agent 只负责调度已有接口、收集证据、结构化到 project_state/artifact_index。

---

## 2. Current Evidence

当前 `project_state/decision_packet.md` 是 Codex 本轮唯一执行权威。`project_state/task_packet.json` 仍是 advisory，不控制本轮。`task_packet/current_state` 中旧 samplereverse 候选和 runtime 线索只作为历史状态，不能覆盖当前 cpp2_883e67b9 工具接入主线。

上一轮 `formula_readiness_audit` 审计结论为 ACCEPTED。当前 artifact_index 中 `local_reverse_cpp2_883e67b9_formula_readiness_audit` provenance 已可核验：

```text
path=project_state\local_reverse_cpp2_883e67b9_formula_readiness_audit.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_formula_readiness_audit_v1
sha256=00de417b4038a95dd27a7fc2edde3ff87b2f6c095697d79a75e209956bc0357a
size_bytes=19181
sample_id=cpp2_883e67b9
overall_formula_readiness=not_ready_static_gaps
solver_profile_normalization_ready=false
reverse_solving_ready=false
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
overall_formula_readiness=not_ready_static_gaps
solver_profile_normalization_ready=false
reverse_solving_ready=false
candidate_generated=false
runtime_validation_attempted=false
recommended_next_mainline=tool_integration

focus comparison loops / contexts:
  loop_0x6081_0x6059: not_ready_static_gaps; exit condition ambiguous; missing inner micro-loops 0x60a4/0x60b6
  loop_0x61e8_0x61b7: not_ready_static_gaps; no direct character constants; relationship to loop_0x6081 unclear
  loop_0x647d_0x62bb: not_ready_static_gaps; unconditional backward jmp; exit branch inside loop unknown

critical gaps:
  focus_loop_exit_condition_unknown
  input_length_unknown
  no_complete_formula_recovered
  known_compare_constant_count_zero
  structured_evidence_ready_false
  missing_backward_sites_unresolved
```

Previous artifact recommends tool_integration: either IDA/Ghidra evidence extraction for focus loops, or focused static re-extraction with capstone/pefile if available. This round chooses the mature-tool path first and must check existing tool interfaces before any new code.

`negative_results.json` still applies: do not return to blind search, do not only increase beam/budget, do not use compare_semantics_agree=false as primary, do not commit full solve_reports, do not treat stale/missing artifacts as current.

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 为 active skill，本轮只使用该 profile。

---

## 3. Do Not Do

严格禁止：

```text
1. 不要进入 reverse_solving。
2. 不要生成 candidate、验证 candidate、运行 negative control 或 runtime validation。
3. 不要 attach debugger / hook / emulator / probe / winpty。
4. 不要运行样本交互逻辑。
5. 不要 brute force、dictionary search、fuzz、扩大枚举预算。
6. 不要回到 old sample_solver blind search。
7. 不要把 cpp2_883e67b9 推进到 candidate 层。
8. 不要把任何 loop/constant 标为 confirmed formula source，除非 IDA/Ghidra/current tool output 直接证明。
9. 不要把 reverse_solving_ready 标为 true，除非 current tool output 已直接提供完整公式、输入长度/终止机制和 candidate construction basis。
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
3. 有界检查相关源码以确认已有 IDA/Ghidra/静态提取接口和避免重复造轮子。
4. 如果已有接口可用，执行 bounded IDA/Ghidra/headless static extraction，仅限指定 focus range 和 focus RVAs。
5. 如果工具不可用，产出 BLOCKED_TOOL_UNAVAILABLE artifact，而不是新建重复工具接口。
6. 新增 project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json。
7. 更新 artifact_index.json 登记新 artifact，包含真实 sha256/size_bytes。
8. 更新 codex_execution_report.md 和 pytest_result.txt。
9. 执行显式 JSON parse 校验。
10. 如确有必要，补充小范围 project_state artifact registration 测试。
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

project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
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
reverse_agent/skills.py
scripts/ 或 tools/ 下所有 ida、idapython、ghidra、headless、objdump、radare2、capstone、pefile 相关文件
tests/test_project_state.py
tests/test_local_reverse_solver_profiles.py
tests/test_local_reverse_solver_profile_dispatch.py
```

必要时搜索：

```text
IDA
IDAPython
ida_guided
Ghidra
ghidra
headless
analyzeHeadless
objdump
radare2
r2
capstone
pefile
StructuredEvidence
artifact_index
local_reverse_cpp2_883e67b9
focus_loop
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
6. 是否检查了已有 IDA / IDAPython / Ghidra / headless / objdump / radare2 / capstone / pefile / StructuredEvidence 接口？
7. 是否复用了已有接口/格式，而非新建重复框架？
8. 如果 IDA/Ghidra 静态接口执行了，命令是什么、范围是否限定在 focus range/RVAs？
9. 如果工具不可用，是否产出 BLOCKED_TOOL_UNAVAILABLE 且未伪造提取结果？
10. 是否读取并只使用 current 的 cpp2_883e67b9 source artifacts？
11. 新 artifact 是否记录 source artifacts/source_run/freshness？
12. 新 artifact 是否覆盖 loop_0x6081_0x6059、loop_0x61e8_0x61b7、loop_0x647d_0x62bb 以及指定 focus RVAs？
13. 新 artifact 是否记录真实工具输出来源、函数边界、basic blocks、branch targets、operands、calls/constants、pseudocode_if_available？
14. 新 artifact 是否避免把任何 loop/constant 标为 confirmed formula source，除非工具输出直接证明？
15. 新 artifact 是否保持 candidate_generated=false、runtime_validation_attempted=false？
16. 新 artifact 是否保持 reverse_solving_ready=false，除非工具输出直接提供完整公式、输入长度/终止机制和 candidate basis？
17. artifact_index 是否登记新 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值？
18. 是否没有修改 training_status/status_overlay？
19. 是否没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG？
20. 是否没有修改 solver production code？如果修改了，为什么必须修改？
21. 是否运行 JSON parse 校验？
22. 是否运行 py_compile？
23. 是否运行相关 pytest？结果是多少？
24. 是否运行 lint-decision、lint-report、project_state status？
25. 是否运行 git diff --check、git status --short、git diff --name-status？
26. git diff 是否只包含允许文件？
```

---

## 6. Implementation Scope

### Phase A — Inspect current source artifacts only

读取并摘要：

```text
project_state/local_reverse_cpp2_883e67b9_formula_readiness_audit.json
project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json
project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json
project_state/local_reverse_cpp2_883e67b9_missing_branch_reconciliation.json
project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json
project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json
project_state/local_reverse_cpp2_883e67b9_targeted_static_solving.json
project_state/local_reverse_cpp2_883e67b9_bounded_static_extraction.json
```

只使用 artifact 内已有证据，不读取 full solve_reports，不回到旧样本求解路径。

### Phase B — Capability and interface audit

有界检查仓库内已有接口：

```text
reverse_agent/local_reverse_ida_guided_solver.py
reverse_agent/local_reverse_constraint_recovery.py
reverse_agent/local_reverse_solver_profiles.py
reverse_agent/project_state.py
reverse_agent/skills.py
scripts/ 或 tools/ 中所有 IDA/Ghidra/headless/objdump/radare2/capstone/pefile 相关文件
```

输出 `tool_capability_check`：

```json
{
  "ida_interface_found": true,
  "ida_interface_path": "...",
  "ida_executable_configured": false,
  "ghidra_interface_found": false,
  "ghidra_headless_configured": false,
  "fallback_static_tools": {
    "objdump": "available|missing|not_checked",
    "radare2": "available|missing|not_checked",
    "capstone": "available|missing|not_checked",
    "pefile": "available|missing|not_checked"
  },
  "selected_static_extraction_path": "ida|ghidra|objdump|radare2|capstone_pefile|blocked_tool_unavailable",
  "reasoning": "..."
}
```

### Phase C — Bounded static extraction, only if existing interface is available

If and only if existing IDA/Ghidra/static extraction interface is available and configured, execute it with scope limited to:

```text
sample_id=cpp2_883e67b9
range=0x5f00-0x6500
focus_rvas=[0x6059,0x6077,0x6081,0x60a3,0x60b5,0x61b7,0x61bd,0x61de,0x61e8,0x61f0,0x6290,0x6294,0x629f,0x62a7,0x62b2,0x62cb,0x6438,0x645f,0x647d,0x64b2,0x64e5]
```

Collect only static evidence:

```text
function boundaries
basic block boundaries
instruction bytes / mnemonic / operands
branch target resolution
xref in/out
calls inside loops
constants and memory operands
stack/register variable hints
decompiler pseudocode if available
```

Do not run the program. Do not attach a debugger. Do not hook. Do not validate candidate.

### Phase D — Create extraction artifact

Generate:

```text
project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json
```

Allowed statuses:

```text
SUCCESS_STATIC_EVIDENCE_EXTRACTED
PARTIAL_STATIC_EVIDENCE_EXTRACTED
BLOCKED_TOOL_UNAVAILABLE
BLOCKED_INTERFACE_MISSING
BLOCKED_SCOPE_WOULD_EXPAND
```

If blocked, artifact must still be valid JSON and must explain exact missing tool/interface/configuration.

### Phase E — Update artifact_index and report

Update:

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index must add:

```text
local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction
```

latest_artifacts_v2 entry must include:

```text
kind=local_reverse_ida_ghidra_focus_loop_extraction
path=project_state\local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json
freshness=current
source_run=round_20260608_cpp2_883e67b9_ida_ghidra_focus_loop_extraction_v1
sample_id=cpp2_883e67b9
relative_path=逆向课程2024春02/CPP2.exe
sha256=<真实值>
size_bytes=<真实值>
extraction_status=SUCCESS_STATIC_EVIDENCE_EXTRACTED|PARTIAL_STATIC_EVIDENCE_EXTRACTED|BLOCKED_TOOL_UNAVAILABLE|BLOCKED_INTERFACE_MISSING|BLOCKED_SCOPE_WOULD_EXPAND
selected_static_extraction_path=ida|ghidra|objdump|radare2|capstone_pefile|blocked_tool_unavailable
reverse_solving_ready=false unless directly supported by extracted static evidence
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
.venv\Scripts\python -c "import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_ida_ghidra_focus_loop_extraction.json', encoding='utf-8'))"
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果执行了 IDA/Ghidra/headless/static extraction command，必须在 report 中记录命令、范围、输出 artifact、退出码；但不要把 full tool dump 写进 project_state，必要时只登记路径与摘要。

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
10. 新 artifact 把 reverse_solving_ready 标为 true，但没有 current extracted static evidence 支持。
11. 新 artifact 把任何 focus loop/constant 标为 confirmed formula source，但没有 current extracted static evidence 支持。
12. artifact_index 无法登记新 artifact 的 current provenance、真实 sha256 或真实 size_bytes。
13. 新 artifact JSON parse 失败。
14. lint-report/status 无法通过。
15. git diff 包含允许范围外文件且报告没有充分理由。
```

完成后不要继续 reverse_solving。若 `extraction_status` 为 BLOCKED_TOOL_UNAVAILABLE 或 BLOCKED_INTERFACE_MISSING，下一轮应修复/接入现有成熟工具配置；若 `SUCCESS_STATIC_EVIDENCE_EXTRACTED` 但 `reverse_solving_ready=false`，下一轮继续 tool_integration 做 StructuredEvidence normalization；只有提取证据明确足够时，下一轮才评估是否进入 reverse_solving。
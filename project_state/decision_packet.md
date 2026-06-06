```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1",
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

目标：基于 current `cpp2_2f64e68d` static triage artifact 中的 IDA 静态证据，生成一个 direct-`strcmp` static handoff artifact。该 handoff 只表达静态候选，不做 runtime validation，不写 `known_candidate`，不标记 solved。

当前 static triage 已经发现 `_main_0` 中存在 `_strcmp` 调用：

```text
call_ea=0x40111C
caller_func=_main_0
callee=_strcmp
nearby="jmp short loc_4010D0 || push offset Str2; \"ippio\" || lea ecx, [ebp+Str1] || push ecx; Str1"
solver_profile_hypotheses=string_compare_password_checker, standard_input_based, strcmp_direct_compare
```

本轮预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
```

预期登记：

```text
artifact_index.latest_artifacts.local_reverse_cpp2_2f64e68d_strcmp_handoff
artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_strcmp_handoff
```

预期 static candidate 字段：

```text
static_candidate_text=ippio
static_candidate_hex=697070696f
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
```

`static_candidate_text=ippio` 只能来自 current triage artifact 的 `_main_0` / `_strcmp` / literal operand 证据，不能来自人工硬编码。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，并且 `execution_scope=decision_packet_controls_current_round`。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮 local reverse 事实以 current artifact 和 artifact_index 为准。

上一轮 schema rework 已审计接受：

```text
report_id=report_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
round_id=round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 已闭合：

```text
status=PASSED
lint-decision=OK
readonly_consistency_check=cpp2 static triage schema rework consistency OK
pytest_project_state=158 passed
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 `artifact_index.json` 已登记 current static triage artifact：

```text
local_reverse_cpp2_2f64e68d_static_triage:
  kind=local_reverse_single_sample_static_triage
  path=project_state\local_reverse_cpp2_2f64e68d_static_triage.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
  sample_id=cpp2_2f64e68d
```

当前 `project_state/local_reverse_cpp2_2f64e68d_static_triage.json` 关键字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
analysis_mode=local_reverse_single_sample_static_triage
source_artifact_freshness=current
mainline=tool_integration
status=STATIC_TRIAGE_COMPLETE
executed_sample=false
static_only=true
runtime_validated=false
solved=false
ida_attempted=true
ida_success=true
source_tool=IDA
tool_status=success
blocked_reason=""
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
size_bytes=196689
queue_rank=1
candidate=null
known_candidate=""
```

当前 static triage 证据：

```text
input_apis=["__input"]
interesting_strings contains "Please input a string : "
functions contains _main_0
compare_contexts[0]:
  call_ea=0x40111C
  caller_func=_main_0
  callee=_strcmp
  call_disasm="call    _strcmp"
  nearby="jmp short loc_4010D0 || push offset Str2; \"ippio\" || lea ecx, [ebp+Str1] || push ecx; Str1"
compare_contexts[1] is CRT/global heap strncmp and must not be used as candidate source.
validation_function_candidates includes _main_0 with reason compare_context | local_check_context | interesting_string_xref.
solver_profile_hypotheses=["string_compare_password_checker", "standard_input_based", "strcmp_direct_compare"]
```

已有能力检查：

```text
1. IDA/IDAPython runner 已存在，且上一轮已成功生成 current static triage artifact；本轮不需要重跑 IDA。
2. reverse_agent/local_reverse_single_sample_static_triage.py 已存在，但本轮不是重新 triage。
3. reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py 是样本专属 XOR handoff，可作为 artifact/report 风格参考，但不得复用其样本硬编码方式。
4. 当前缺口是 direct-strcmp static candidate handoff：从 current triage artifact 的 compare_context 中提取 literal expected string。
5. 不要新增反汇编器、PE parser、debugger 或重复 IDA/Ghidra 接口。
```

当前 `negative_results.json` 仍禁止：

```text
1. old sample_solver blind search
2. only increase guided_pool beam or budget
3. use compare_semantics_agree=false candidates as primary frontier
4. commit full solve_reports directory
5. repeat dynamic-probe directions without new evidence
6. run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不触碰旧 samplereverse 搜索、beam、Base64/RC4、CompareProbe、runtime probe、debugger 或 brute force。

---

## 3. Do Not Do

严禁：

```text
1. 不运行目标样本。
2. 不做 runtime validation。
3. 不运行 IDA/Ghidra。
4. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
5. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
6. 不把 static_candidate_text 写入 known_candidate。
7. 不设置 solved=true。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
9. 不修改 local_reverse_training_status.json。
10. 不修改 local_reverse_evaluation_queue.json。
11. 不修改 training_materials/local_reverse/status_overlay.json。
12. 不修改 cpp1_7b504c54 的任何 artifact。
13. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
14. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
15. 不为 `ippio` 写样本硬编码逻辑。
16. 不使用 CRT/global heap `_strncmp` context 中的 `__GLOBAL_HEAP_SELECTED` 作为候选来源。
17. 不把 static handoff 当作 runtime proof。
```

允许：

```text
1. 新增一个轻量、可复用的 direct-strcmp static handoff 脚本，例如 reverse_agent/local_reverse_direct_strcmp_handoff.py。
2. 新增对应测试，例如 tests/test_local_reverse_direct_strcmp_handoff.py。
3. 脚本只读取 current triage artifact，从 compare_contexts 中选择 caller_func=_main_0 且 callee=_strcmp 的 context，解析 literal operand。
4. 生成 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
5. 更新 project_state/artifact_index.json 登记 handoff artifact。
6. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
.codex-skills/registry.json
```

必须检查可复用实现参考：

```text
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
reverse_agent/local_reverse_single_sample_static_triage.py
```

按需读取：

```text
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_single_sample_static_triage.py
pyproject.toml
requirements.txt
requirements-dev.txt
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
4. 是否确认本轮目标样本是 cpp2_2f64e68d。
5. 是否确认 source static triage artifact 为 current。
6. 是否确认 source static triage artifact status=STATIC_TRIAGE_COMPLETE、source_tool=IDA、solved=false。
7. 是否确认 direct strcmp context 来源为 caller_func=_main_0、callee=_strcmp、call_ea=0x40111C。
8. 是否确认未使用 CRT/global heap `_strncmp` context 作为候选来源。
9. 是否确认 static_candidate_text 是从 compare_context.nearby literal 解析得出，不是硬编码。
10. 是否确认没有运行目标样本。
11. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
12. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
13. 是否确认没有写 known_candidate、没有标记 solved=true。
14. 是否确认生成 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
15. 是否确认 artifact_index.latest_artifacts 与 latest_artifacts_v2 已登记 handoff artifact。
16. 是否确认 handoff artifact freshness=current，source_run=round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1。
17. 是否确认未修改 source static triage artifact、训练状态、队列、overlay、cpp1 artifact。
18. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
19. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

建议实现：

```text
1. 新增 reverse_agent/local_reverse_direct_strcmp_handoff.py。
2. 该模块应通用处理 direct strcmp 静态 handoff，不要写死 sample_id=cpp2_2f64e68d 或 literal=ippio。
3. 输入：--triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
4. 选择 compare context 的规则：
   - callee 精确属于 {"_strcmp", "strcmp"}；
   - 优先 caller_func == "_main_0"；
   - 排除 callee 为 _strncmp / strncmp 的 CRT/global heap context；
   - nearby 中必须包含 literal 形式 `"..."`；
   - literal 不能是 CRT/debug/global heap/internal marker；
   - context 必须能识别一边是 stack/local input，例如 `lea ecx, [ebp+Str1]` 或 `push ecx; Str1`。
5. 解析结果应得出 static_candidate_text=ippio，static_candidate_hex=697070696f。
```

handoff artifact 最低字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
analysis_mode=direct_strcmp_static_handoff
mainline=reverse_solving
source_artifacts=["local_reverse_cpp2_2f64e68d_static_triage"]
source_artifact_freshness=current
source_triage_artifact=project_state/local_reverse_cpp2_2f64e68d_static_triage.json
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
executed_sample=false
static_only=true
runtime_validated=false
source_tool=IDA
compare_call_ea=0x40111C
compare_caller_func=_main_0
compare_callee=_strcmp
compare_nearby=<original nearby string>
input_operand_summary="stack/local input Str1"
expected_operand_summary="literal string Str2"
static_candidate_text=ippio
static_candidate_hex=697070696f
static_candidate_printable=true
extraction_method=direct_strcmp_literal_operand
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
status=READY_FOR_RUNTIME_VALIDATION
blocked_reason=""
generated_at=<UTC>
```

若不能 safely extract：

```text
status=BLOCKED
blocked_reason one of NO_CURRENT_STATIC_TRIAGE / NO_DIRECT_STRCMP_CONTEXT / AMBIGUOUS_STRCMP_CONTEXT / NO_LITERAL_EXPECTED_OPERAND / INTERNAL_CRT_CONTEXT_ONLY
static_candidate_text=""
static_candidate_hex=""
candidate=null
known_candidate=""
solved=false
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_strcmp_handoff = "project_state\\local_reverse_cpp2_2f64e68d_strcmp_handoff.json"

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_strcmp_handoff = {
  kind="local_reverse_direct_strcmp_handoff",
  path="project_state\\local_reverse_cpp2_2f64e68d_strcmp_handoff.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<current UTC timestamp>,
  sample_id="cpp2_2f64e68d"
}
```

允许修改：

```text
reverse_agent/local_reverse_direct_strcmp_handoff.py
tests/test_local_reverse_direct_strcmp_handoff.py
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
reverse_agent/olly_scripts/*
.codex-skills/*
solve_reports/*
project_state/triage_*
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m py_compile reverse_agent/local_reverse_direct_strcmp_handoff.py
python -m pytest -q tests/test_local_reverse_direct_strcmp_handoff.py
python -m reverse_agent.local_reverse_direct_strcmp_handoff --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
python - <<'PY'
import json
from pathlib import Path
handoff=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
triage=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_static_triage.json').read_text(encoding='utf-8'))
assert triage['sample_id']=='cpp2_2f64e68d'
assert triage['source_artifact_freshness']=='current'
assert triage['status']=='STATIC_TRIAGE_COMPLETE'
assert handoff['schema_version']==1
assert handoff['sample_id']=='cpp2_2f64e68d'
assert handoff['analysis_mode']=='direct_strcmp_static_handoff'
assert handoff['mainline']=='reverse_solving'
assert handoff['source_artifact_freshness']=='current'
assert handoff['executed_sample'] is False
assert handoff['static_only'] is True
assert handoff['runtime_validated'] is False
assert handoff['compare_call_ea']=='0x40111C'
assert handoff['compare_caller_func']=='_main_0'
assert handoff['compare_callee']=='_strcmp'
assert handoff['static_candidate_text']=='ippio'
assert handoff['static_candidate_hex']=='697070696f'
assert handoff['static_candidate_printable'] is True
assert handoff['candidate'] is None
assert handoff['known_candidate']==''
assert handoff['validation_status']=='not_validated'
assert handoff['solved'] is False
assert handoff['status']=='READY_FOR_RUNTIME_VALIDATION'
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_strcmp_handoff']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_direct_strcmp_handoff'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1'
print('cpp2 direct strcmp handoff consistency OK')
PY
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议追加：

```bash
python -m pytest -q tests/test_project_state.py
```

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED/BLOCKED 结果；
5. 本轮 decision_id、round_id、report_id。
```

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. current static triage artifact 缺失或不是 sample_id=cpp2_2f64e68d。
2. artifact_index 中 local_reverse_cpp2_2f64e68d_static_triage 缺失或 freshness 不是 current。
3. static triage artifact 的 status 不是 STATIC_TRIAGE_COMPLETE 或 source_tool 不是 IDA。
4. 没有 caller_func=_main_0 且 callee=_strcmp 的 compare context。
5. 只能找到 CRT/global heap _strncmp context。
6. direct strcmp literal operand 不唯一或无法区分 input operand 与 expected operand。
7. 需要重新运行 IDA/Ghidra 才能继续。
8. 需要运行目标样本、runtime validation、debugger、hook、emulator、CompareProbe 才能继续。
9. 需要修改 source static triage artifact、训练状态、队列、overlay 或 cpp1 artifact 才能继续。
10. 需要写 known_candidate 或 solved=true 才能继续。
11. lint-report 或 project_state status 无法闭合。
12. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. direct strcmp static handoff artifact 已生成。
2. static_candidate_text=ippio 只来自 current static triage compare_context.literal operand。
3. artifact 明确 candidate=null、known_candidate=""、validation_status=not_validated、solved=false。
4. artifact_index 登记 handoff artifact 为 current。
5. 未运行样本、未运行 IDA/Ghidra、未做 runtime。
6. 未修改 static triage artifact、训练状态、队列、overlay 或 cpp1 artifact。
7. report/pytest_result 与本 decision_id/round_id 匹配。
8. 所有测试与 git 检查真实记录。
```

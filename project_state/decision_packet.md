```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260605_cpp1_7b504c54_xor_handoff_v1",
  "round_id": "round_20260605_cpp1_7b504c54_xor_handoff_v1",
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

目标：基于 current `cpp1_7b504c54` static triage artifact 中 `_main_0` 的双 XOR 结构，做一次有界的 **static XOR inverse handoff**：提取并校验 `byte_427A30`、`byte_427A3C`、`byte_427A48` 三组 10-byte 静态数组，按已确认公式生成静态候选，并输出可审计 handoff artifact。

当前 `_main_0` 静态证据显示：

```text
input length check: strlen(Str) == 10
for i in 0..9: v4[i + 20] = byte_427A30[9 - i] ^ Str[i]
for i in 0..9: v4[i] = byte_427A3C[i] ^ v4[i + 20]
for i in 0..9: compare v4[i] == byte_427A48[i]
```

因此静态逆公式是：

```text
Str[i] = byte_427A30[9 - i] ^ byte_427A3C[i] ^ byte_427A48[i]
```

本轮只允许静态提取、静态逆推和 artifact 生成。不得运行样本、不得 runtime validation、不得标记 solved、不得把静态候选写入 `known_candidate`。如果得到 candidate，只能写入 `static_candidate_text` / `static_candidate_hex`，并保持：

```text
known_candidate=""
runtime_validated=false
validation_status=not_validated
solved=false
```

预期新增文件：

```text
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
```

并更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 登记要求：

```text
artifact key=local_reverse_cpp1_7b504c54_xor_handoff
kind=local_reverse_cpp1_xor_handoff
path=project_state\local_reverse_cpp1_7b504c54_xor_handoff.json
freshness=current
source_run=round_20260605_cpp1_7b504c54_xor_handoff_v1
sample_id=cpp1_7b504c54
```

---

## 2. Current Evidence

当前 `task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮；当前执行权威是 `project_state/decision_packet.md`。

当前 `current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 report/pytest 返工已闭合：

```text
report_id=report_20260605_cpp1_7b504c54_static_triage_report_rework_v1
based_on_decision_id=decision_20260605_cpp1_7b504c54_static_triage_report_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 `project_state/local_reverse_cpp1_7b504c54_static_triage.json` 为 current 静态证据：

```text
sample_id=cpp1_7b504c54
analysis_mode=single_sample_static_triage
mainline=tool_integration
executed_sample=false
static_only=true
runtime_validated=false
tool_status=success
source_tool=IDA
sha256=7b504c54c165100549a0eacb7eb7cad26bc235ec0c4bed5c38c95a827ff81a3c
queue_rank=1
candidate=null
known_candidate=""
```

其中 `_main_0` decompiler snippet 为：

```c
printf("Please give me your input:\n");
sub_401005(Str, 15);
if ( strlen(Str) == 10 )
{
  for ( i = 0; i < 10; ++i )
    v4[i + 20] = byte_427A30[9 - i] ^ Str[i];
  for ( i = 0; i < 10; ++i )
    v4[i] = byte_427A3C[i] ^ v4[i + 20];
  for ( i = 0; i < 10 && v4[i] == byte_427A48[i]; ++i )
    ;
  if ( i == 10 )
    printf("Congratulations! You are right!\n");
  else
    printf("Sorry, you are wrong!\n");
}
```

当前 `artifact_index.json` 已登记：

```text
local_reverse_cpp1_7b504c54_static_triage:
  kind=local_reverse_single_sample_static_triage
  path=project_state\local_reverse_cpp1_7b504c54_static_triage.json
  freshness=current
  source_run=round_20260605_cpp1_7b504c54_static_triage_v1
  sample_id=cpp1_7b504c54
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

本轮不触碰这些方向。

已有相关能力检查：

```text
1. 已有 `reverse_agent/local_reverse_single_sample_static_triage.py`，可产生静态 triage artifact；本轮不得重复运行，除非只读验证且不改 artifact。
2. 已有 `reverse_agent/tool_runners.py` 和 IDA resolver；不得新建第二套 IDA runner。
3. 已有 `reverse_agent/ida_scripts/collect_evidence.py`；如需补充静态数组 bytes，必须复用现有 tool_runners/IDA script 模式，或优先从现有 triage artifact / PE raw data 中提取。
4. 当前没有专门的 `cpp1_7b504c54` 三数组 XOR handoff 脚本；允许新增一个小型、样本限定的 handoff 模块，但不得写成长期通用 skill 或硬编码进训练集逻辑。
```

---

## 3. Do Not Do

严禁：

```text
1. 不动态执行样本。
2. 不做 runtime validation。
3. 不运行 debugger/runtime probe/hook/emulator。
4. 不运行 brute force、guided pool、old sample_solver。
5. 不扩大 beam/topN/budget/timeout。
6. 不标记 solved。
7. 不写 `known_candidate`。
8. 不把 static candidate 当 validated candidate。
9. 不修改 `project_state/local_reverse_cpp1_7b504c54_static_triage.json`。
10. 不修改 `project_state/local_reverse_training_status.json`。
11. 不修改 `project_state/local_reverse_evaluation_queue.json`。
12. 不修改 `training_materials/local_reverse/status_overlay.json`。
13. 不修改 `.codex-skills`。
14. 不提交本地 binary、IDA sidecar、raw temp、`project_state/triage_*` 或 full solve_reports。
15. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
16. 不新建第二套 IDA runner。
17. 不把 `cpp1_2f6fcb63` 的证据迁移到 `cpp1_7b504c54`。
18. 不把旧 samplereverse task_packet 当执行权威。
```

允许：

```text
1. 读取 current static triage artifact。
2. 读取 artifact_index / training status / queue 作为状态背景。
3. 新增一个样本限定的 static XOR handoff 脚本。
4. 新增对应 pytest。
5. 如现有 artifact 已包含足够 decompiler evidence，但没有 raw bytes，可从本地 PE raw data 静态读取三组数组；不得提交 binary 或本地绝对路径。
6. 如必须使用 IDA 提取数组 bytes，只能复用现有 tool_runners/collect_evidence 模式，且必须说明是 bounded static extraction，不是动态执行。
7. 生成 static handoff artifact，并登记 artifact_index。
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
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
.codex-skills/registry.json
```

按需读取：

```text
reverse_agent/local_reverse_cpp1_target_byte_extract.py
reverse_agent/local_reverse_cpp1_inverse_handoff.py
reverse_agent/local_reverse_cpp1_transform_recheck.py
reverse_agent/local_reverse_cpp1_signed_transform_recheck.py
# 仅作已有 cpp1 workflow 风格参考；不得复用旧样本 artifact 当当前证据。
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
4. 是否确认本轮只处理 `cpp1_7b504c54`。
5. 是否确认使用的是 current `local_reverse_cpp1_7b504c54_static_triage.json`，且 freshness=current。
6. 是否确认 `_main_0` 的双 XOR 结构来自 current static triage artifact。
7. 是否确认提取到 `byte_427A30`、`byte_427A3C`、`byte_427A48` 三组 10-byte 数组，或明确 blocked_reason。
8. 是否说明三组数组的来源：triage artifact / PE raw data / bounded IDA static extraction。
9. 如果使用 IDA，是否确认只是 bounded static extraction，且没有新建 IDA runner。
10. 是否确认没有动态执行样本，没有 runtime validation。
11. 是否确认没有 debugger/runtime probe/hook/emulator。
12. 是否确认没有 brute force / guided pool / old sample_solver。
13. 是否确认没有修改 static triage artifact。
14. 是否确认没有修改 training_status / evaluation_queue。
15. 是否确认没有写 `known_candidate`。
16. 是否确认没有标记 solved。
17. 是否确认 static candidate 如果存在，只写入 `static_candidate_text` / `static_candidate_hex`，并标记 `validation_status=not_validated`。
18. 是否生成 `project_state/local_reverse_cpp1_7b504c54_xor_handoff.json`。
19. 是否将该 artifact 登记到 `artifact_index.json`，freshness=current，source_run=round_20260605_cpp1_7b504c54_xor_handoff_v1。
20. 是否 `codex_report_summary.generated_artifacts` 包含本轮生成/重写的 project_state artifacts。
21. 是否 `pytest_result.txt` 记录每条命令、Exit Code 和输出摘要。
22. 是否 `git status --short` 和 `git diff --name-status` 只包含允许文件。
```

---

## 6. Implementation Scope

允许新增：

```text
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
```

允许修改：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
reverse_agent/local_reverse_single_sample_static_triage.py
reverse_agent/tool_runners.py
reverse_agent/ida_scripts/collect_evidence.py
.codex-skills/*
solve_reports/*
project_state/triage_*
```

`local_reverse_cpp1_7b504c54_xor_handoff.json` 至少包含：

```text
schema_version
sample_id=cpp1_7b504c54
analysis_mode=cpp1_7b504c54_static_xor_handoff
mainline=reverse_solving
executed_sample=false
static_only=true
runtime_validated=false
source_artifacts
source_artifact_freshness
source_triage_artifact=project_state/local_reverse_cpp1_7b504c54_static_triage.json
main_function=_main_0
main_entry_ea=0x401110
input_length=10
transform_formula="candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]"
arrays.byte_427A30.address=0x427A30
arrays.byte_427A30.bytes_hex
arrays.byte_427A3C.address=0x427A3C
arrays.byte_427A3C.bytes_hex
arrays.byte_427A48.address=0x427A48
arrays.byte_427A48.bytes_hex
static_candidate_hex
static_candidate_text
static_candidate_printable=true|false
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
recommended_next_action
status=READY_FOR_STATIC_REVIEW | BLOCKED
blocked_reason
```

如果三组数组无法静态提取，artifact 必须：

```text
status=BLOCKED
blocked_reason=MISSING_STATIC_ARRAY_BYTES 或更具体原因
static_candidate_hex=""
static_candidate_text=""
known_candidate=""
runtime_validated=false
solved=false
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
python -m pytest -q tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
python -m reverse_agent.local_reverse_cpp1_7b504c54_xor_handoff --static-triage project_state/local_reverse_cpp1_7b504c54_static_triage.json --out project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果 CLI 需要 `--binary-root` 或 `--sample-root` 才能静态读取 PE raw data，必须通过环境变量或参数读取，但不得把真实本地绝对路径写入 artifact / report。

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
1. current static triage artifact 缺失或 artifact_index freshness 不是 current。
2. `_main_0` 双 XOR 结构无法从 current static triage artifact 中确认。
3. 需要动态执行样本才能继续。
4. 需要 runtime validation 才能继续。
5. 需要 debugger/runtime probe/hook/emulator。
6. 需要 brute force / guided pool / old sample_solver。
7. 需要提交本地 binary、IDA sidecar、raw temp、triage temp dir 或 full solve_reports。
8. 需要修改 static triage artifact、training_status 或 evaluation_queue。
9. 无法静态提取三组数组，且没有 current bounded static extraction 证据。
10. `lint-report` 或 `project_state status` 无法在当前 report 下通过。
```

成功完成的最低标准：

```text
1. 生成 `project_state/local_reverse_cpp1_7b504c54_xor_handoff.json`。
2. 明确记录三组数组 bytes 或明确 blocked_reason。
3. 若生成 static candidate，必须标为 not_validated，不写 known_candidate，不标记 solved。
4. artifact_index 登记 current artifact。
5. report/pytest/status 全部闭合。
6. git diff 只包含允许文件。
```

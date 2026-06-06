```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_runtime_pair_validation_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1",
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

目标：对 `cpp2_2f64e68d` 的 current static direct-`strcmp` candidate 做有界 runtime validation。由于 current static triage 中没有可靠的 success/failure token，本轮不得直接套用 token-only validator；应执行 **paired console validation**：只运行 static candidate `ippio` 与一个同长度 negative control，对比 stdout/stderr/return code，保守判断验证状态。

本轮允许执行目标样本，但仅限以下输入：

```text
candidate_input=ippio
negative_control=<由 ippio 派生的同长度错误输入，例如 jppio 或 xppio；必须与 ippio 不同>
max_runs=2
```

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
```

预期登记：

```text
artifact_index.latest_artifacts.local_reverse_cpp2_2f64e68d_runtime_pair_validation
artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_runtime_pair_validation
```

成功判定必须保守：只有当 candidate run 和 negative-control run 都真实执行，且输出/退出码差异能明确支持 candidate 被接受、negative control 被拒绝，才允许在 runtime validation artifact 中写：

```text
validation_status=VALIDATED_SUCCESS
candidate=ippio
known_candidate=ippio
solved=true
```

若目标文件缺失、Windows runtime 不可用、超时、输出无差异、输出语义不清、或者只能得到 prompt 而无明确接受/拒绝信号，则必须写：

```text
validation_status=BLOCKED or AMBIGUOUS_OUTPUT
known_candidate=""
solved=false
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，且 `execution_scope=decision_packet_controls_current_round`。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮 local reverse 事实以 current artifacts 与 artifact_index 为准。

上一轮 direct strcmp handoff 已审计接受：

```text
report_id=report_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1
round_id=round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 已闭合：

```text
status=PASSED
lint-decision=OK
py_compile=OK
pytest_direct_strcmp_handoff=6 passed
direct_strcmp_handoff: READY_FOR_RUNTIME_VALIDATION, static_candidate_text=ippio
readonly_consistency_check=cpp2 direct strcmp handoff consistency OK
pytest_project_state=158 passed
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

当前 artifact_index 已登记 current source artifacts：

```text
local_reverse_cpp2_2f64e68d_static_triage:
  kind=local_reverse_single_sample_static_triage
  path=project_state\local_reverse_cpp2_2f64e68d_static_triage.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_static_triage_schema_rework_v1
  sample_id=cpp2_2f64e68d

local_reverse_cpp2_2f64e68d_strcmp_handoff:
  kind=local_reverse_direct_strcmp_handoff
  path=project_state\local_reverse_cpp2_2f64e68d_strcmp_handoff.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_direct_strcmp_handoff_v1
  sample_id=cpp2_2f64e68d
```

当前 static triage artifact 关键事实：

```text
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
analysis_mode=local_reverse_single_sample_static_triage
source_artifact_freshness=current
status=STATIC_TRIAGE_COMPLETE
executed_sample=false
static_only=true
runtime_validated=false
solved=false
source_tool=IDA
tool_status=success
blocked_reason=""
```

当前 direct strcmp handoff artifact 关键事实：

```text
path=project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
sample_id=cpp2_2f64e68d
analysis_mode=direct_strcmp_static_handoff
mainline=reverse_solving
source_artifact_freshness=current
source_triage_artifact=project_state/local_reverse_cpp2_2f64e68d_static_triage.json
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
executed_sample=false
static_only=true
runtime_validated=false
source_tool=IDA
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
compare_call_ea=0x40111C
compare_caller_func=_main_0
compare_callee=_strcmp
static_candidate_text=ippio
static_candidate_hex=697070696f
static_candidate_printable=true
status=READY_FOR_RUNTIME_VALIDATION
blocked_reason=""
```

已有能力检查：

```text
1. reverse_agent/local_reverse_console_validator.py 已存在，是 token-based console validator，能解析 target path、校验 sha256、stdin 写 candidate + newline + newline、捕获 stdout/stderr/return code。
2. 该 validator 需要 success_token/failure_token/length_token；cpp2 current static triage 中没有可靠 success/failure token，因此不能强行使用 token-only 模式作为 solved 判据。
3. 可以新增 thin pair validator，例如 reverse_agent/local_reverse_console_pair_validator.py；应尽量复用 local_reverse_console_validator.py 中的 target path resolution、sha256 helper 和 subprocess 思路，不重写 PE/IDA/solver 能力。
4. 不需要重跑 IDA/Ghidra；current static triage 与 strcmp handoff 已足够作为 candidate 来源。
5. 不需要 debugger、hook、emulator、CompareProbe 或 brute force。
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

本轮不是旧 samplereverse 搜索，也不是 brute force；本轮只做 2-run candidate/control validation。

---

## 3. Do Not Do

严禁：

```text
1. 不重跑 IDA/Ghidra。
2. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
3. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
4. 不测试超过 2 个输入。
5. 不枚举、爆破、变异多候选。
6. 不修改 static triage artifact。
7. 不修改 strcmp handoff artifact。
8. 不修改 local_reverse_training_status.json。
9. 不修改 local_reverse_evaluation_queue.json。
10. 不修改 training_materials/local_reverse/status_overlay.json。
11. 不修改 cpp1_7b504c54 的任何 artifact。
12. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
13. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
14. 不在输出语义不清时写 known_candidate 或 solved=true。
15. 不把 static_candidate_text=ippio 本身当作 runtime proof。
16. 不把 TARGET_MISSING / UNSUPPORTED_RUNTIME / TIMEOUT / AMBIGUOUS_OUTPUT 当作候选反证。
```

允许：

```text
1. 新增 thin paired console validator，例如 reverse_agent/local_reverse_console_pair_validator.py。
2. 新增对应单元测试，例如 tests/test_local_reverse_console_pair_validator.py。
3. 复用现有 console validator 的 target path resolution 与 sha256 helper。
4. 对 cpp2 只运行 candidate_input=ippio 和一个同长度 negative_control。
5. 生成 project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json。
6. 更新 artifact_index.json 登记 runtime pair validation artifact。
7. 更新 codex_execution_report.md 与 pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
.codex-skills/registry.json
reverse_agent/local_reverse_console_validator.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
```

按需读取：

```text
tests/test_local_reverse_direct_strcmp_handoff.py
tests/test_local_reverse_console_validator.py
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
4. 是否确认目标样本为 cpp2_2f64e68d。
5. 是否确认 source static triage artifact 为 current 且 status=STATIC_TRIAGE_COMPLETE。
6. 是否确认 source strcmp handoff artifact 为 current 且 status=READY_FOR_RUNTIME_VALIDATION。
7. 是否确认 candidate_input 仅来自 handoff.static_candidate_text=ippio。
8. 是否确认 negative_control 与 ippio 同长度且不同。
9. 是否确认最多运行 2 次目标样本。
10. 是否确认未运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
11. 是否确认未运行 solver/bruteforce/guided pool/symbolic search。
12. 是否确认未修改 static triage artifact 或 strcmp handoff artifact。
13. 是否确认未修改 training status、evaluation queue、status overlay 或 cpp1 artifacts。
14. 是否确认 runtime validation artifact 记录 candidate/control 的 stdout_tail、stderr_tail、return_code、timed_out、executed flags。
15. 如果 solved=true，是否明确说明 candidate accepted 与 negative control rejected 的具体输出/退出码证据。
16. 如果输出无差异或语义不清，是否设置 AMBIGUOUS_OUTPUT/BLOCKED 且 solved=false。
17. 是否确认 artifact_index.latest_artifacts 与 latest_artifacts_v2 登记 runtime pair validation artifact。
18. 是否确认 artifact freshness=current，source_run=round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
21. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

建议实现：

```text
1. 新增 reverse_agent/local_reverse_console_pair_validator.py。
2. 复用 reverse_agent/local_reverse_console_validator.py 的 _resolve_target_path 与 _sha256_file。
3. 输入：
   --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json
   --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
   --candidate-field static_candidate_text
   --out project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
4. 自动生成 negative_control：保持同长度，修改首个可打印字符；例如 ippio -> jppio 或 xppio。
5. 对 candidate 与 negative_control 各运行一次，stdin 均写 input + "\n\n"。
6. 捕获 stdout/stderr/return_code/timeout。
7. 仅做 pair comparison；不要枚举其他输入。
```

runtime pair validation artifact 最低字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
analysis_mode=console_runtime_pair_validation
mainline=reverse_solving
source_artifacts=["local_reverse_cpp2_2f64e68d_strcmp_handoff", "local_reverse_cpp2_2f64e68d_static_triage"]
source_artifact_freshness=current
source_candidate_artifact=project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
source_triage_artifact=project_state/local_reverse_cpp2_2f64e68d_static_triage.json
relative_path=逆向课程2025春03/CPP2.exe
sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
candidate_source_field=static_candidate_text
candidate_input=ippio
negative_control_input=<same length, not ippio>
negative_control_strategy=single_char_mutation
max_runs=2
executed_sample=true/false
runtime_validated=true/false
validation_status=VALIDATED_SUCCESS / VALIDATED_FAILURE / AMBIGUOUS_OUTPUT / BLOCKED
candidate_run={input, executed, timed_out, return_code, stdout_tail, stderr_tail}
negative_control_run={input, executed, timed_out, return_code, stdout_tail, stderr_tail}
outputs_differ=true/false
success_reason="..."
failure_reason="..."
candidate=ippio or null
known_candidate=ippio or ""
solved=true/false
blocked_reason="" or TARGET_MISSING / TARGET_MISMATCH / UNSUPPORTED_RUNTIME / TIMEOUT / AMBIGUOUS_OUTPUT / CANDIDATE_MISSING
control_rejected=true/false
candidate_accepted=true/false
generated_at=<UTC>
```

状态语义：

```text
VALIDATED_SUCCESS:
  candidate_run.executed=true
  negative_control_run.executed=true
  outputs_differ=true
  candidate_accepted=true
  control_rejected=true
  runtime_validated=true
  candidate=ippio
  known_candidate=ippio
  solved=true
  success_reason 必须引用具体 stdout/stderr/return_code 差异

VALIDATED_FAILURE:
  candidate_run.executed=true
  negative_control_run.executed=true
  candidate clearly rejected, 或 candidate output 与 failure/control rejection output 一致
  candidate=null
  known_candidate=""
  solved=false

AMBIGUOUS_OUTPUT:
  candidate/control 都执行，但输出无差异、只有 prompt、无明确接受/拒绝语义，或无法保守判断
  candidate=null
  known_candidate=""
  solved=false

BLOCKED:
  target missing, target sha mismatch, unsupported runtime, timeout, candidate missing, dependency error
  candidate=null
  known_candidate=""
  solved=false
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_runtime_pair_validation = "project_state\\local_reverse_cpp2_2f64e68d_runtime_pair_validation.json"

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_runtime_pair_validation = {
  kind="local_reverse_console_pair_runtime_validation",
  path="project_state\\local_reverse_cpp2_2f64e68d_runtime_pair_validation.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<current UTC timestamp>,
  sample_id="cpp2_2f64e68d"
}
```

允许修改：

```text
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/local_reverse_direct_strcmp_handoff.py
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
python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
python -m pytest -q tests/test_local_reverse_console_pair_validator.py
python -m reverse_agent.local_reverse_console_pair_validator --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --candidate-field static_candidate_text --out project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
handoff=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json').read_text(encoding='utf-8'))
assert handoff['sample_id']=='cpp2_2f64e68d'
assert handoff['source_artifact_freshness']=='current'
assert handoff['static_candidate_text']=='ippio'
assert handoff['known_candidate']==''
assert handoff['solved'] is False
assert v['schema_version']==1
assert v['sample_id']=='cpp2_2f64e68d'
assert v['analysis_mode']=='console_runtime_pair_validation'
assert v['mainline']=='reverse_solving'
assert v['source_artifact_freshness']=='current'
assert v['candidate_source_field']=='static_candidate_text'
assert v['candidate_input']=='ippio'
assert v['negative_control_input'] != 'ippio'
assert len(v['negative_control_input']) == len('ippio')
assert v['max_runs']==2
assert v['validation_status'] in ('VALIDATED_SUCCESS','VALIDATED_FAILURE','AMBIGUOUS_OUTPUT','BLOCKED')
assert v['candidate'] in (None, 'ippio')
assert v['known_candidate'] in ('', 'ippio')
if v['solved']:
    assert v['validation_status']=='VALIDATED_SUCCESS'
    assert v['runtime_validated'] is True
    assert v['candidate']=='ippio'
    assert v['known_candidate']=='ippio'
    assert v['candidate_accepted'] is True
    assert v['control_rejected'] is True
else:
    assert v['known_candidate']==''
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_runtime_pair_validation']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_console_pair_runtime_validation'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1'
print('cpp2 runtime pair validation consistency OK')
PY
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
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
1. source static triage artifact 缺失或不是 current。
2. source strcmp handoff artifact 缺失或不是 current。
3. handoff.static_candidate_text 不是 ippio 或 candidate/known_candidate/solved 已被提前提升。
4. 无法生成同长度 negative_control。
5. 需要运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe 才能继续。
6. 需要超过 2 次目标样本运行才可判断。
7. 需要修改 source static triage artifact 或 strcmp handoff artifact 才能继续。
8. 需要修改训练状态、队列、overlay 或 cpp1 artifact 才能继续。
9. target missing / unsupported runtime / timeout 无法被清晰记录为 BLOCKED。
10. candidate/control 输出无明确差异却试图写 solved=true。
11. lint-report 或 project_state status 无法闭合。
12. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. runtime pair validation artifact 已生成并登记 current。
2. 只运行 candidate 与一个同长度 negative control，最多 2 次目标样本执行。
3. 若 solved=true，必须有 candidate accepted 与 control rejected 的具体 runtime 证据。
4. 若证据不清，必须保守写 AMBIGUOUS_OUTPUT/BLOCKED 且 solved=false。
5. 未重跑 IDA/Ghidra，未运行 debugger/hook/emulator/CompareProbe，未运行 solver/bruteforce。
6. 未修改 source static triage artifact、strcmp handoff artifact、训练状态、队列、overlay 或 cpp1 artifacts。
7. report/pytest_result 与本 decision_id/round_id 匹配。
8. 所有测试与 git 检查真实记录。
```

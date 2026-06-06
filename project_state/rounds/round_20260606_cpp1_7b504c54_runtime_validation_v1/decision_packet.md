```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp1_7b504c54_runtime_validation_v1",
  "round_id": "round_20260606_cpp1_7b504c54_runtime_validation_v1",
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

目标：对 `cpp1_7b504c54` 的 current static candidate 做有界 runtime validation，并把验证结果写成可审计 artifact。上一轮只完成 report/metadata 修复；当前 `project_state/local_reverse_cpp1_7b504c54_xor_handoff.json` 仍是 static-only，不能直接当 solved 结果。

本轮允许：

```text
1. 读取 current static triage 与 XOR handoff artifact。
2. 新增一个可复用的 console runtime validator，用于 stdin/stdout 型本地 PE 样本验证。
3. 用 validator 仅验证 handoff artifact 中的 static_candidate_text=WeKnowItOk。
4. 生成 project_state/local_reverse_cpp1_7b504c54_runtime_validation.json。
5. 更新 project_state/artifact_index.json 登记 runtime validation artifact。
6. 如果且仅如果目标进程真实执行且 stdout/stderr 中观察到 success token，可在 runtime validation artifact 中设置 candidate/known_candidate/solved=true。
```

本轮不做训练集批量推进，不进入旧 `samplereverse` 路线，不扩大到其他样本。

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory：`task=Review bounded window discovery diagnostics`，并明确 `project_state/decision_packet.md` 才是当前轮执行权威。`task_packet.task` 不控制本轮。

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮有关 `cpp1_7b504c54` 的事实以 `artifact_index.json`、`local_reverse_cpp1_7b504c54_static_triage.json`、`local_reverse_cpp1_7b504c54_xor_handoff.json` 为准。

当前上一轮 Codex 报告已经闭合：

```text
report_id=report_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
based_on_decision_id=decision_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
round_id=round_20260605_cpp1_7b504c54_xor_handoff_report_metadata_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

当前 `pytest_result.txt` 记录：

```text
status=PASSED
Total Commands=7
Passed=7
Failed=0
lint-report=OK
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
readonly_consistency_check: arrays match, kind=local_reverse_cpp1_xor_handoff
```

当前 static triage artifact：

```text
path=project_state/local_reverse_cpp1_7b504c54_static_triage.json
sample_id=cpp1_7b504c54
relative_path=逆向课程2023春补考01/Cpp1.exe
source_tool=IDA
executed_sample=false
static_only=true
runtime_validated=false
source_artifact_freshness=current
main_function=_main_0
main_entry_ea=0x401110
```

IDA decompiler snippet 已给出核心逻辑：

```text
printf("Please give me your input:\n");
sub_401005(Str, 15);
if ( strlen(Str) == 10 ) {
  for i in 0..9: v4[i + 20] = byte_427A30[9 - i] ^ Str[i]
  for i in 0..9: v4[i] = byte_427A3C[i] ^ v4[i + 20]
  for i in 0..9 && v4[i] == byte_427A48[i]
  if i == 10: printf("Congratulations! You are right!\n")
  else: printf("Sorry, you are wrong!\n")
  system("pause")
} else {
  printf("Sorry, the length is wrong!\n")
  system("pause")
}
```

当前 XOR handoff artifact：

```text
path=project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
sample_id=cpp1_7b504c54
analysis_mode=cpp1_7b504c54_static_xor_handoff
executed_sample=false
static_only=true
runtime_validated=false
source_artifact_freshness=current
input_length=10
transform_formula="candidate[i] = byte_427A30[9-i] ^ byte_427A3C[i] ^ byte_427A48[i]"
byte_427A30.bytes_hex=0102030405060708090a
byte_427A3C.bytes_hex=1112131415161718191a
byte_427A48.bytes_hex=4c7e507d7c645a6f5470
static_candidate_hex=57654b6e6f7749744f6b
static_candidate_text=WeKnowItOk
static_candidate_printable=true
forward_transform_verified=true
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
status=READY_FOR_STATIC_REVIEW
```

当前 `artifact_index.json` 已登记 current artifacts：

```text
local_reverse_cpp1_7b504c54_static_triage:
  kind=local_reverse_single_sample_static_triage
  path=project_state\local_reverse_cpp1_7b504c54_static_triage.json
  freshness=current
  source_run=round_20260605_cpp1_7b504c54_static_triage_v1
  sample_id=cpp1_7b504c54

local_reverse_cpp1_7b504c54_xor_handoff:
  kind=local_reverse_cpp1_xor_handoff
  path=project_state\local_reverse_cpp1_7b504c54_xor_handoff.json
  freshness=current
  source_run=round_20260605_cpp1_7b504c54_xor_handoff_v1
  sample_id=cpp1_7b504c54
```

已有工具接口检查：

```text
1. IDA/IDAPython: reverse_agent/tool_runners.py 已有 run_ida_evidence 与 ida_scripts/collect_evidence.py；当前 static triage 已来自 IDA，不需要本轮重新运行 IDA。
2. OllyDbg/debugger: reverse_agent/tool_runners.py 有 OllyDbg/CompareProbe 接口，但当前样本是 console stdin/stdout 型 Cpp1.exe，不是 GUI 宽字符串 compare_probe 场景。
3. CompareProbe: reverse_agent/olly_scripts/compare_probe.py 依赖 frida + pywinauto + GUI 控件 auto_id，目标是 samplereverse GUI compare capture；本轮不得用它硬套 console 样本。
4. Static XOR handoff: reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py 是 static-only，文件头明确 Does NOT execute target binary / Does NOT validate at runtime。
5. 当前缺口：缺少一个小型、可复用的 console candidate runtime validator。
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

本轮不触碰旧 samplereverse 搜索/beam/Base64/RC4/compare-probe 方向；本轮只验证当前 `cpp1_7b504c54` 的单个 static candidate。

---

## 3. Do Not Do

严禁：

```text
1. 不回到 old sample_solver blind search。
2. 不扩 beam/topN/budget/timeout 来碰运气。
3. 不运行 IDA/Ghidra；current static evidence 已足够。
4. 不运行 OllyDbg、Frida hook、CompareProbe、debugger、emulator。
5. 不把 reverse_agent/olly_scripts/compare_probe.py 硬套到当前 console 样本。
6. 不重新生成或修改 project_state/local_reverse_cpp1_7b504c54_xor_handoff.json。
7. 不重新生成或修改 project_state/local_reverse_cpp1_7b504c54_static_triage.json。
8. 不修改 .codex-skills。
9. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
10. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
11. 不批量处理 local_reverse_samples / E:\reverse 下其他样本。
12. 不修改其他样本状态。
13. 不把 static_candidate_text 直接写入 global known_candidate。
14. 不在未观察到真实 success output 时标记 solved=true。
15. 不把 timeout、target missing、unsupported runtime 当作验证失败；这些只能是 BLOCKED/NOT_VALIDATED。
16. 不把 stdout 中的 prompt 或 length message 当作成功。
```

允许：

```text
1. 新增通用 console runtime validator 模块，例如 reverse_agent/local_reverse_console_validator.py。
2. 新增对应单元测试，例如 tests/test_local_reverse_console_validator.py。
3. 运行 validator 对 cpp1_7b504c54 的 static_candidate_text=WeKnowItOk 做单候选 runtime validation。
4. 生成 project_state/local_reverse_cpp1_7b504c54_runtime_validation.json。
5. 更新 project_state/artifact_index.json，登记 local_reverse_cpp1_7b504c54_runtime_validation。
6. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
7. 如果且仅如果 runtime validation 成功，可在 runtime validation artifact 中记录 candidate/known_candidate/solved=true；不要修改 static handoff artifact。
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
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
.codex-skills/registry.json
reverse_agent/tool_runners.py
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
```

必须检查但不应默认使用：

```text
reverse_agent/olly_scripts/compare_probe.py
```

按需读取：

```text
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
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
4. 是否确认 current static triage artifact 与 XOR handoff artifact 均为 current。
5. 是否确认 source_tool=IDA 且本轮不需要重跑 IDA/Ghidra。
6. 是否确认已有 OllyDbg/CompareProbe 接口不适合当前 console sample，并未使用。
7. 是否确认没有运行 debugger/hook/emulator/CompareProbe。
8. 是否确认没有回到 old sample_solver blind search。
9. 是否确认只验证 handoff artifact 中的单个 static_candidate_text。
10. 是否确认 validator 是 stdin/stdout console validation，不包含样本专属硬编码算法。
11. 是否确认没有修改 static triage artifact。
12. 是否确认没有修改 XOR handoff artifact。
13. 是否确认 runtime validation artifact 明确记录 executed_sample/runtime_validated/validation_status/solved/blocked_reason。
14. 如果成功，是否确认 stdout/stderr 中观察到 exact success token: "Congratulations! You are right!"。
15. 如果失败，是否区分 wrong candidate、target missing、unsupported runtime、timeout、ambiguous output。
16. 是否确认没有把 blocked/timeout/ambiguous 当作 solved=false 的候选反证。
17. 是否确认 artifact_index 新增/更新 key=local_reverse_cpp1_7b504c54_runtime_validation，freshness=current，sample_id=cpp1_7b504c54，source_run=round_20260606_cpp1_7b504c54_runtime_validation_v1。
18. 是否确认 project_state/codex_execution_report.md 顶部 codex_report_summary 与本 decision_id/round_id 匹配。
19. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
20. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

建议实现：

```text
1. 新增 reverse_agent/local_reverse_console_validator.py
   - 输入：triage artifact、candidate artifact、candidate field、success token、failure token、timeout、output path。
   - 解析 triage.relative_path，并复用 LOCAL_REVERSE_ROOT / E:\reverse / D:\reverse / C:\reverse / ~/reverse 的路径查找逻辑。
   - 只通过 subprocess 启动目标，向 stdin 写入 candidate + newline + newline，以覆盖 system("pause")。
   - 捕获 stdout/stderr/returncode。
   - 超时必须 kill process。
   - 输出 JSON artifact。

2. 新增 tests/test_local_reverse_console_validator.py
   - 用临时 Python 子进程或 mock subprocess 测试 success/failure/target_missing/timeout/ambiguous。
   - 不依赖本地 E:\reverse 或真实 PE。

3. 运行实际验证命令：
   python -m reverse_agent.local_reverse_console_validator \
     --triage project_state/local_reverse_cpp1_7b504c54_static_triage.json \
     --candidate-artifact project_state/local_reverse_cpp1_7b504c54_xor_handoff.json \
     --candidate-field static_candidate_text \
     --success-token "Congratulations! You are right!" \
     --failure-token "Sorry, you are wrong!" \
     --length-token "Sorry, the length is wrong!" \
     --out project_state/local_reverse_cpp1_7b504c54_runtime_validation.json

4. 更新 project_state/artifact_index.json：
   latest_artifacts.local_reverse_cpp1_7b504c54_runtime_validation = project_state\\local_reverse_cpp1_7b504c54_runtime_validation.json
   latest_artifacts_v2.local_reverse_cpp1_7b504c54_runtime_validation = {
     kind=local_reverse_console_runtime_validation,
     path=project_state\\local_reverse_cpp1_7b504c54_runtime_validation.json,
     freshness=current,
     source_run=round_20260606_cpp1_7b504c54_runtime_validation_v1,
     sha256=<actual file sha256>,
     size_bytes=<actual size>,
     modified_at=<actual UTC timestamp>,
     sample_id=cpp1_7b504c54
   }

5. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
```

允许修改：

```text
reverse_agent/local_reverse_console_validator.py
tests/test_local_reverse_console_validator.py
project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp1_7b504c54_xor_handoff.json
project_state/local_reverse_cpp1_7b504c54_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
reverse_agent/local_reverse_cpp1_7b504c54_xor_handoff.py
tests/test_local_reverse_cpp1_7b504c54_xor_handoff.py
reverse_agent/tool_runners.py
reverse_agent/olly_scripts/compare_probe.py
.codex-skills/*
solve_reports/*
project_state/triage_*
```

Runtime validation artifact 最低字段：

```text
schema_version
sample_id
analysis_mode=console_runtime_validation
mainline=reverse_solving
source_artifacts
source_artifact_freshness
relative_path
candidate_source_field
candidate
known_candidate
executed_sample
runtime_validated
validation_status
success_token
failure_token
length_token
success_observed
failure_observed
length_error_observed
return_code
stdout_tail
stderr_tail
solved
blocked_reason
generated_at
```

状态语义：

```text
VALIDATED_SUCCESS:
  executed_sample=true
  runtime_validated=true
  success_observed=true
  candidate=WeKnowItOk
  known_candidate=WeKnowItOk
  solved=true

VALIDATED_FAILURE:
  executed_sample=true
  runtime_validated=true
  success_observed=false
  failure_observed=true or length_error_observed=true
  candidate=null
  known_candidate=""
  solved=false

BLOCKED:
  executed_sample=false or runtime_validated=false
  validation_status=blocked
  candidate=null
  known_candidate=""
  solved=false
  blocked_reason one of TARGET_MISSING / UNSUPPORTED_RUNTIME / TIMEOUT / DEPENDENCY_ERROR / AMBIGUOUS_OUTPUT / CANDIDATE_MISSING
```

---

## 7. Tests

必须运行并记录：

```bash
python -m py_compile reverse_agent/local_reverse_console_validator.py
python -m pytest -q tests/test_local_reverse_console_validator.py
python -m reverse_agent.local_reverse_console_validator --triage project_state/local_reverse_cpp1_7b504c54_static_triage.json --candidate-artifact project_state/local_reverse_cpp1_7b504c54_xor_handoff.json --candidate-field static_candidate_text --success-token "Congratulations! You are right!" --failure-token "Sorry, you are wrong!" --length-token "Sorry, the length is wrong!" --out project_state/local_reverse_cpp1_7b504c54_runtime_validation.json
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

建议追加只读 consistency check：

```bash
python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('project_state/local_reverse_cpp1_7b504c54_runtime_validation.json').read_text(encoding='utf-8'))
i=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
assert v['sample_id']=='cpp1_7b504c54'
assert v['candidate'] in (None, 'WeKnowItOk')
assert v['known_candidate'] in ('', 'WeKnowItOk')
assert v['solved'] in (False, True)
if v['solved']:
    assert v['validation_status']=='VALIDATED_SUCCESS'
    assert v['runtime_validated'] is True
    assert v['success_observed'] is True
    assert v['known_candidate']=='WeKnowItOk'
entry=i['latest_artifacts_v2']['local_reverse_cpp1_7b504c54_runtime_validation']
assert entry['freshness']=='current'
assert entry['sample_id']=='cpp1_7b504c54'
assert entry['kind']=='local_reverse_console_runtime_validation'
assert entry['source_run']=='round_20260606_cpp1_7b504c54_runtime_validation_v1'
PY
```

`pytest_result.txt` 必须包含：

```text
1. 每条命令原文；
2. Exit Code；
3. 输出摘要；
4. PASSED/FAILED/BLOCKED 结果；
5. 本轮 decision_id、round_id、report_id。
```

如果真实 PE 或 Windows runtime 不可用，validator 命令可以生成 BLOCKED artifact，但 Codex 报告必须是 `status=BLOCKED` 或 `status=PARTIAL`，不得写 `acceptance_recommendation=ACCEPTED`。

---

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED`：

```text
1. project_state/local_reverse_cpp1_7b504c54_xor_handoff.json 缺失或无法解析。
2. project_state/local_reverse_cpp1_7b504c54_static_triage.json 缺失或无法解析。
3. artifact_index 中 current handoff/static_triage 缺失或 freshness 不是 current。
4. handoff artifact 的 static_candidate_text 缺失、不是 10 字符、或 forward_transform_verified=false。
5. 需要修改 handoff artifact 或 static triage artifact 才能继续。
6. 需要运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe 才能继续。
7. 目标 binary 缺失且 validator 无法生成清晰 BLOCKED artifact。
8. 运行目标超时且无法安全终止进程。
9. stdout/stderr 同时不能确认 success/failure/length/timeout，且 artifact 没有标记 AMBIGUOUS_OUTPUT。
10. lint-report 或 project_state status 无法闭合。
11. git diff 包含 forbidden files。
```

成功完成的最低标准：

```text
1. 新增的 console validator 有单元测试覆盖。
2. runtime validation artifact 已生成，且状态语义清晰。
3. artifact_index 已登记 current runtime validation artifact。
4. 没有修改 static triage 或 XOR handoff artifact。
5. 没有使用 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
6. 如果 solved=true，必须有真实 success token 证据。
7. lint-decision/lint-report/status 和 git 检查全部记录到 pytest_result.txt。
```

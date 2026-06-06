```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_interaction_probe_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_interaction_probe_v1",
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

目标：在 `cpp2_2f64e68d` 的 pipe-stdin runtime pair validation 已经得到 `AMBIGUOUS_OUTPUT` 后，新增一个有界的 Windows 真实控制台交互能力探针，用于判断项目是否具备下一轮通过 ConPTY/TTY-like console 方式重测该类 console API / packed PE 样本的条件。

本轮只做能力探针和证据记录，不重新验证 `ippio`，不运行 `CPP2.exe`，不改 candidate、known_candidate 或 solved 状态。

当前问题：

```text
runtime_pair_validation 使用 subprocess pipe stdin。
candidate=ippio 与 negative_control=jppio 均输出：
  "Please input a string : \nSorry! Hang on!"
return_code 均为 4294967295。
outputs_differ=false。
validation_status=AMBIGUOUS_OUTPUT。
```

合理推断：该样本可能依赖真实 console/ReadConsole/packed wrapper 行为，pipe stdin 不足以构成有效 runtime proof。下一步不能重复 pipe-stdin pair validation；必须先建立或判定真实控制台交互能力。

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_console_interaction_probe.json
```

预期登记：

```text
artifact_index.latest_artifacts.local_reverse_cpp2_2f64e68d_console_interaction_probe
artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_console_interaction_probe
```

本轮成功标准不是 solved，而是明确回答：

```text
1. 当前运行环境是否是 Windows。
2. 是否可用 ConPTY / pseudo-console / pty-like mechanism。
3. 项目是否已有可复用 console-interaction runner 能力。
4. 如果可用，下一轮是否允许对 cpp2 做最多 2-run ConPTY candidate/control validation。
5. 如果不可用，是否把 cpp2 标记为等待 Windows interactive-console capability，而不是继续重复 pipe runtime。
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，并且 `execution_scope=decision_packet_controls_current_round`。`task_packet.task` 不控制本轮。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮 local reverse 事实以 current artifacts 与 artifact_index 为准。

上一轮 report rework 已审计接受：

```text
report_id=report_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1
round_id=round_20260606_cpp2_2f64e68d_runtime_pair_validation_report_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮 `pytest_result.txt` 已闭合：

```text
status=PASSED
lint-report Exit Code=0
decision_consumed_by_report=True
decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
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

local_reverse_cpp2_2f64e68d_runtime_pair_validation:
  kind=local_reverse_console_pair_runtime_validation
  path=project_state\local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
  freshness=current
  source_run=round_20260606_cpp2_2f64e68d_runtime_pair_validation_v1
  sample_id=cpp2_2f64e68d
```

Current runtime pair validation artifact：

```text
sample_id=cpp2_2f64e68d
analysis_mode=console_runtime_pair_validation
candidate_input=ippio
negative_control_input=jppio
max_runs=2
executed_sample=true
runtime_validated=false
validation_status=AMBIGUOUS_OUTPUT
outputs_differ=false
candidate=null
known_candidate=""
solved=false
blocked_reason=AMBIGUOUS_OUTPUT
candidate_accepted=false
control_rejected=false
target_resolved_path=E:\reverse\逆向课程2025春03\CPP2.exe
```

Current static handoff artifact：

```text
sample_id=cpp2_2f64e68d
analysis_mode=direct_strcmp_static_handoff
source_artifact_freshness=current
compare_call_ea=0x40111C
compare_caller_func=_main_0
compare_callee=_strcmp
static_candidate_text=ippio
candidate=null
known_candidate=""
validation_status=not_validated
solved=false
status=READY_FOR_RUNTIME_VALIDATION
```

当前已有工具能力：

```text
1. reverse_agent/local_reverse_console_pair_validator.py 已存在，使用 subprocess pipe stdin。
2. pipe stdin pair validation 对 cpp2 得到 AMBIGUOUS_OUTPUT，不能重复作为新增证据。
3. 目前未确认项目是否有 ConPTY / pty-like interactive console runner。
4. IDA/IDAPython 静态证据已 current，本轮不需要重跑 IDA。
5. OllyDbg/CompareProbe 是 GUI/hook 方向，不适合本轮作为默认路径。
```

当前 negative_results 仍禁止：

```text
old sample_solver blind search
only increase guided_pool beam or budget
compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
repeat dynamic-probe directions without new evidence
run Base64/RC4 breakpoint probe before real lhs producer identification
```

本轮不是重复 dynamic probe；本轮只做 console-interaction capability probe，不运行 CPP2.exe，不验证候选。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不重新运行 reverse_agent.local_reverse_console_pair_validator。
3. 不运行 IDA/Ghidra。
4. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
5. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
6. 不测试任何 candidate/control 输入。
7. 不修改 project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
9. 不修改 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
10. 不修改 project_state/local_reverse_training_status.json。
11. 不修改 project_state/local_reverse_evaluation_queue.json。
12. 不修改 training_materials/local_reverse/status_overlay.json。
13. 不修改 cpp1_7b504c54 的任何 artifact。
14. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
15. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
16. 不把 AMBIGUOUS_OUTPUT 当作 solved。
17. 不写 known_candidate=ippio。
18. 不设置 solved=true。
19. 不把 ConPTY capability available 当作 candidate validation proof。
```

允许：

```text
1. 新增 thin capability probe，例如 reverse_agent/local_reverse_console_interaction_probe.py。
2. 新增对应测试，例如 tests/test_local_reverse_console_interaction_probe.py。
3. 只做环境与接口探测：platform、Windows version hint、ConPTY API availability、fallback pty support、是否可构造 command plan。
4. 可用临时 toy process / Python echo fixture 测试 probe 代码，但不得运行 CPP2.exe。
5. 生成 project_state/local_reverse_cpp2_2f64e68d_console_interaction_probe.json。
6. 更新 artifact_index.json 登记 probe artifact。
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
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
.codex-skills/registry.json
reverse_agent/local_reverse_console_pair_validator.py
```

按需读取：

```text
tests/test_local_reverse_console_pair_validator.py
pyproject.toml
requirements.txt
requirements-dev.txt
README.md
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
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮是 console interaction capability probe，不是 runtime validation。
5. 是否确认没有运行 CPP2.exe。
6. 是否确认没有运行 pair validator。
7. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
8. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
9. 是否确认没有修改 runtime_pair_validation artifact。
10. 是否确认没有修改 static triage artifact 或 strcmp handoff artifact。
11. 是否确认没有修改 training status、queue、overlay 或 cpp1 artifacts。
12. 是否确认 probe artifact 记录 runtime_pair_validation 当前为 AMBIGUOUS_OUTPUT / solved=false。
13. 是否确认 probe artifact 记录 pipe stdin path 已经不足以提供 proof，下一步必须使用 non-pipe interactive-console evidence 才能重测。
14. 是否确认 probe artifact 明确 conpty_available / pty_available / windows_platform / recommended_next_action。
15. 如果环境不是 Windows，是否记录 BLOCKED_NON_WINDOWS_ENVIRONMENT，而不是尝试运行 CPP2.exe。
16. 如果 Windows 但 ConPTY 不可用，是否记录 BLOCKED_NO_CONPTY。
17. 如果 capability 可用，是否只建议下一轮最多 2-run ConPTY validation，不在本轮执行。
18. 是否确认 artifact_index.latest_artifacts 与 latest_artifacts_v2 登记 console_interaction_probe artifact。
19. 是否确认 artifact freshness=current，source_run=round_20260606_cpp2_2f64e68d_console_interaction_probe_v1。
20. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
21. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
22. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

建议实现：

```text
1. 新增 reverse_agent/local_reverse_console_interaction_probe.py。
2. 该模块只做 capability probe，不运行目标样本。
3. 可提供函数：
   - detect_console_interaction_capability()
   - build_next_validation_recommendation(runtime_artifact, handoff_artifact)
   - write_probe_artifact(...)
4. Windows 上检查：
   - platform.system() == "Windows"
   - ctypes.windll.kernel32 是否有 CreatePseudoConsole / ClosePseudoConsole / ResizePseudoConsole。
   - 不实际创建 CPP2 子进程。
5. 非 Windows 上检查：
   - pty module 是否可 import。
   - 但对 PE/CPP2 仍应返回 BLOCKED_NON_WINDOWS_ENVIRONMENT。
6. 读取 current runtime_pair_validation artifact，确认 validation_status=AMBIGUOUS_OUTPUT、solved=false、known_candidate=""。
7. 读取 current strcmp handoff artifact，确认 static_candidate_text=ippio、status=READY_FOR_RUNTIME_VALIDATION。
8. 输出 probe artifact。
```

probe artifact 最低字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
analysis_mode=console_interaction_capability_probe
mainline=tool_integration
source_artifacts=["local_reverse_cpp2_2f64e68d_runtime_pair_validation", "local_reverse_cpp2_2f64e68d_strcmp_handoff", "local_reverse_cpp2_2f64e68d_static_triage"]
source_artifact_freshness=current
runtime_pair_validation_artifact=project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
strcmp_handoff_artifact=project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
static_triage_artifact=project_state/local_reverse_cpp2_2f64e68d_static_triage.json
candidate_input=ippio
previous_validation_status=AMBIGUOUS_OUTPUT
previous_outputs_differ=false
previous_runtime_validated=false
previous_known_candidate=""
previous_solved=false
windows_platform=true/false
platform_system=<value>
conpty_api_available=true/false
pty_module_available=true/false
can_attempt_interactive_console_validation_next=true/false
probe_status=READY_FOR_CONPTY_VALIDATION / BLOCKED_NON_WINDOWS_ENVIRONMENT / BLOCKED_NO_CONPTY / BLOCKED_SOURCE_ARTIFACT_MISMATCH
recommended_next_action=<string>
executed_target=false
runtime_validated=false
candidate=null
known_candidate=""
solved=false
blocked_reason="" or one of above
generated_at=<UTC>
```

状态语义：

```text
READY_FOR_CONPTY_VALIDATION:
  Windows platform true; ConPTY API available; current source artifacts valid.
  Does not mean candidate validated.

BLOCKED_NON_WINDOWS_ENVIRONMENT:
  Not Windows. Do not attempt PE interactive console validation in this environment.

BLOCKED_NO_CONPTY:
  Windows but required pseudo-console API unavailable.

BLOCKED_SOURCE_ARTIFACT_MISMATCH:
  current artifacts missing, stale, or not in expected AMBIGUOUS_OUTPUT/not solved state.
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_console_interaction_probe = "project_state\\local_reverse_cpp2_2f64e68d_console_interaction_probe.json"

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_console_interaction_probe = {
  kind="local_reverse_console_interaction_capability_probe",
  path="project_state\\local_reverse_cpp2_2f64e68d_console_interaction_probe.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_console_interaction_probe_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<current UTC timestamp>,
  sample_id="cpp2_2f64e68d"
}
```

允许修改：

```text
reverse_agent/local_reverse_console_interaction_probe.py
tests/test_local_reverse_console_interaction_probe.py
project_state/local_reverse_cpp2_2f64e68d_console_interaction_probe.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_training_status.json
project_state/local_reverse_evaluation_queue.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_cpp1_7b504c54_*.json
reverse_agent/local_reverse_console_pair_validator.py
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
python -m py_compile reverse_agent/local_reverse_console_interaction_probe.py
python -m pytest -q tests/test_local_reverse_console_interaction_probe.py
python -m reverse_agent.local_reverse_console_interaction_probe --runtime-artifact project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json --handoff-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --triage-artifact project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_console_interaction_probe.json
python - <<'PY'
import json
from pathlib import Path
probe=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_console_interaction_probe.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
runtime=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json').read_text(encoding='utf-8'))
assert runtime['sample_id']=='cpp2_2f64e68d'
assert runtime['validation_status']=='AMBIGUOUS_OUTPUT'
assert runtime['known_candidate']==''
assert runtime['solved'] is False
assert probe['schema_version']==1
assert probe['sample_id']=='cpp2_2f64e68d'
assert probe['analysis_mode']=='console_interaction_capability_probe'
assert probe['mainline']=='tool_integration'
assert probe['source_artifact_freshness']=='current'
assert probe['candidate_input']=='ippio'
assert probe['previous_validation_status']=='AMBIGUOUS_OUTPUT'
assert probe['previous_known_candidate']==''
assert probe['previous_solved'] is False
assert probe['executed_target'] is False
assert probe['runtime_validated'] is False
assert probe['known_candidate']==''
assert probe['solved'] is False
assert probe['probe_status'] in ('READY_FOR_CONPTY_VALIDATION','BLOCKED_NON_WINDOWS_ENVIRONMENT','BLOCKED_NO_CONPTY','BLOCKED_SOURCE_ARTIFACT_MISMATCH')
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_console_interaction_probe']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_console_interaction_capability_probe'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_console_interaction_probe_v1'
print('cpp2 console interaction probe consistency OK')
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
1. runtime_pair_validation artifact 缺失或不是 AMBIGUOUS_OUTPUT / solved=false / known_candidate=""。
2. strcmp_handoff artifact 缺失或不是 READY_FOR_RUNTIME_VALIDATION / static_candidate_text=ippio。
3. static_triage artifact 缺失或不是 STATIC_TRIAGE_COMPLETE。
4. artifact_index 中 source artifact freshness 不是 current。
5. 需要运行 CPP2.exe 才能继续。
6. 需要重新运行 pair validator 才能继续。
7. 需要运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe 才能继续。
8. 需要修改 runtime/source artifacts、训练状态、队列、overlay 或 cpp1 artifacts 才能继续。
9. probe artifact 试图写 known_candidate 或 solved=true。
10. git diff 包含 forbidden files。
11. lint-report 或 project_state status 无法闭合。
```

成功完成的最低标准：

```text
1. console interaction capability probe artifact 已生成并登记 current。
2. probe 明确不运行 CPP2.exe，不验证 candidate。
3. probe 明确保留 AMBIGUOUS_OUTPUT / solved=false。
4. probe 给出下一轮是否可执行 ConPTY validation 的条件化建议。
5. 未重复 pipe-stdin validation。
6. 未修改 runtime/source artifacts、训练状态、队列、overlay 或代码外文件。
7. report/pytest_result 与本 decision_id/round_id 匹配。
8. 所有测试与 git 检查真实记录。
```

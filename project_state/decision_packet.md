```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1",
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

目标：把上一版 `console_interaction_probe` 收窄为 **mature backend availability probe**。本轮只检查当前环境是否存在可复用的成熟控制台交互后端，并生成能力探测 artifact；不得自研完整 ConPTY / Expect / terminal emulator / console runner。

当前 `cpp2_2f64e68d` 的 pipe-stdin runtime pair validation 已得到保守结论：

```text
candidate_input=ippio
negative_control_input=jppio
outputs_differ=false
validation_status=AMBIGUOUS_OUTPUT
known_candidate=""
solved=false
```

因此下一步不能重复 pipe-stdin validation。也不能直接写自研交互控制台后端。必须先回答：项目能否通过成熟工具或系统接口进入下一轮 interactive-console validation。

本轮只允许探测并记录这些成熟后端/系统能力是否可用：

```text
1. pywinpty / winpty Python package availability
2. wexpect Python package availability
3. pexpect availability，仅作为 POSIX/文档参考，不用于 Windows PE validation
4. Windows ConPTY API availability，仅检查 CreatePseudoConsole / ClosePseudoConsole / ResizePseudoConsole 是否存在
5. 当前平台信息：platform.system(), sys.platform, os.name
```

本轮严禁实现：

```text
1. 完整 ConPTY runner
2. Expect-like 状态机
3. terminal emulator
4. 自研 CreatePseudoConsole ctypes backend
5. 任何面向 CPP2.exe 的交互执行逻辑
```

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
```

预期登记：

```text
artifact_index.latest_artifacts.local_reverse_cpp2_2f64e68d_console_mature_backend_probe
artifact_index.latest_artifacts_v2.local_reverse_cpp2_2f64e68d_console_mature_backend_probe
```

本轮成功标准不是 solved，而是明确给出：

```text
1. 当前环境是否 Windows。
2. 是否发现可优先使用的成熟 backend：pywinpty / winpty / wexpect。
3. 是否发现 Windows ConPTY API 可用。
4. 如果成熟 backend 可用，下一轮可以设计最多 2-run interactive-console candidate/control validation。
5. 如果成熟 backend 不可用，只能 BLOCKED_MATURE_BACKEND_MISSING，不得要求自研完整 backend。
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，`task=Review bounded window discovery diagnostics`，且 `execution_scope=decision_packet_controls_current_round`。`task_packet.task` 不控制本轮。

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

已有相关能力检查：

```text
1. reverse_agent/local_reverse_console_pair_validator.py 已存在，但它使用 subprocess pipe stdin。
2. pipe stdin pair validation 对 cpp2 已产生 AMBIGUOUS_OUTPUT，不能重复作为新增证据。
3. 当前尚未记录 pywinpty / winpty / wexpect / pexpect / Windows ConPTY API availability。
4. IDA/IDAPython 静态证据已 current，本轮不需要重跑 IDA。
5. OllyDbg/CompareProbe 是 GUI/hook 方向，不适合作为本轮默认路径。
6. 成熟工具优先：不得重复实现 pywinpty/wexpect/ConPTY/Expect 已有能力。
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

本轮不是重复 dynamic probe；本轮只做 mature backend availability probe，不运行 CPP2.exe，不验证候选。

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
19. 不把 ConPTY/API/backend availability 当作 candidate validation proof。
20. 不实现完整 ConPTY runner。
21. 不实现 Expect-like 状态机。
22. 不实现 terminal emulator。
23. 不用 ctypes 大量封装 CreatePseudoConsole 形成自研 backend。
24. 不新增 pywinpty/wexpect/pexpect 到 requirements，除非本轮只记录“missing dependency”并由后续 decision 决定依赖策略。
```

允许：

```text
1. 新增 thin mature backend probe，例如 reverse_agent/local_reverse_console_mature_backend_probe.py。
2. 新增对应测试，例如 tests/test_local_reverse_console_mature_backend_probe.py。
3. 只用 importlib.util.find_spec 探测 pywinpty / winpty / wexpect / pexpect 是否安装。
4. Windows 上只检查 ctypes.windll.kernel32 是否存在 CreatePseudoConsole / ClosePseudoConsole / ResizePseudoConsole；不得创建 pseudo console，不得启动目标进程。
5. 读取 current runtime/static artifacts 做一致性核对。
6. 生成 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
7. 更新 artifact_index.json 登记 probe artifact。
8. 更新 codex_execution_report.md 与 pytest_result.txt。
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
4. 是否确认本轮是 mature backend availability probe，不是 runtime validation。
5. 是否确认成熟工具优先，并且没有自研完整 ConPTY/Expect/terminal backend。
6. 是否确认只探测 pywinpty / winpty / wexpect / pexpect / Windows ConPTY API availability。
7. 是否确认没有运行 CPP2.exe。
8. 是否确认没有运行 pair validator。
9. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
10. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
11. 是否确认没有修改 runtime_pair_validation artifact。
12. 是否确认没有修改 static triage artifact 或 strcmp handoff artifact。
13. 是否确认没有修改 training status、queue、overlay 或 cpp1 artifacts。
14. 是否确认 probe artifact 记录 runtime_pair_validation 当前为 AMBIGUOUS_OUTPUT / solved=false。
15. 是否确认 probe artifact 明确 mature_backend_priority=true。
16. 是否确认 probe artifact 明确 preferred_backend_order，例如 pywinpty/winpty -> wexpect -> Windows ConPTY API presence check -> pexpect POSIX reference。
17. 是否确认 probe artifact 明确 no_custom_conpty_runner=true、no_expect_state_machine=true、no_terminal_emulator=true。
18. 如果成熟 backend 缺失，是否记录 BLOCKED_MATURE_BACKEND_MISSING 或 BLOCKED_NON_WINDOWS_ENVIRONMENT。
19. 如果成熟 backend 可用，是否只建议下一轮最多 2-run interactive-console validation，不在本轮执行。
20. 是否确认 artifact_index.latest_artifacts 与 latest_artifacts_v2 登记 mature backend probe artifact。
21. 是否确认 artifact freshness=current，source_run=round_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1。
22. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
23. 是否确认 pytest_result.txt 记录每条命令、Exit Code 和输出摘要。
24. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

建议实现：

```text
1. 新增 reverse_agent/local_reverse_console_mature_backend_probe.py。
2. 该模块只做 mature backend discovery，不运行目标样本。
3. 可提供函数：
   - detect_python_backend_availability()
   - detect_windows_conpty_api_presence()
   - build_backend_recommendation(runtime_artifact, handoff_artifact, triage_artifact)
   - write_probe_artifact(...)
4. Python package 检测仅用 importlib.util.find_spec，不 import 执行复杂库逻辑。
5. Windows ConPTY API 检测仅检查函数名是否存在，不创建 pseudo console。
6. 读取 current runtime_pair_validation artifact，确认 validation_status=AMBIGUOUS_OUTPUT、solved=false、known_candidate=""。
7. 读取 current strcmp handoff artifact，确认 static_candidate_text=ippio、status=READY_FOR_RUNTIME_VALIDATION。
8. 输出 probe artifact。
```

probe artifact 最低字段：

```text
schema_version=1
sample_id=cpp2_2f64e68d
analysis_mode=console_mature_backend_availability_probe
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
mature_backend_priority=true
preferred_backend_order=["pywinpty_or_winpty", "wexpect", "windows_conpty_api_presence", "pexpect_posix_reference_only"]
pywinpty_available=true/false
winpty_available=true/false
wexpect_available=true/false
pexpect_available=true/false
windows_platform=true/false
platform_system=<value>
sys_platform=<value>
os_name=<value>
conpty_api_available=true/false
conpty_api_checked=true/false
no_custom_conpty_runner=true
no_expect_state_machine=true
no_terminal_emulator=true
can_attempt_interactive_console_validation_next=true/false
probe_status=READY_FOR_MATURE_BACKEND_VALIDATION / BLOCKED_NON_WINDOWS_ENVIRONMENT / BLOCKED_MATURE_BACKEND_MISSING / BLOCKED_SOURCE_ARTIFACT_MISMATCH
recommended_backend=<string or "">
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
READY_FOR_MATURE_BACKEND_VALIDATION:
  source artifacts valid;
  Windows platform true;
  at least one mature Windows-capable backend available: pywinpty/winpty/wexpect or ConPTY API available;
  does not mean candidate validated.

BLOCKED_NON_WINDOWS_ENVIRONMENT:
  Not Windows. Do not attempt PE interactive console validation here.

BLOCKED_MATURE_BACKEND_MISSING:
  Windows but no mature backend/package/API availability found.

BLOCKED_SOURCE_ARTIFACT_MISMATCH:
  current artifacts missing, stale, or not in expected AMBIGUOUS_OUTPUT/not-solved state.
```

必须更新 artifact_index：

```text
latest_artifacts.local_reverse_cpp2_2f64e68d_console_mature_backend_probe = "project_state\\local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json"

latest_artifacts_v2.local_reverse_cpp2_2f64e68d_console_mature_backend_probe = {
  kind="local_reverse_console_mature_backend_availability_probe",
  path="project_state\\local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json",
  freshness="current",
  source_run="round_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1",
  sha256=<actual file sha256>,
  size_bytes=<actual size>,
  modified_at=<current UTC timestamp>,
  sample_id="cpp2_2f64e68d"
}
```

允许修改：

```text
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
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
requirements.txt
requirements-dev.txt
pyproject.toml
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
python -m reverse_agent.local_reverse_console_mature_backend_probe --runtime-artifact project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json --handoff-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --triage-artifact project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
python - <<'PY'
import json
from pathlib import Path
probe=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json').read_text(encoding='utf-8'))
index=json.loads(Path('project_state/artifact_index.json').read_text(encoding='utf-8'))
runtime=json.loads(Path('project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json').read_text(encoding='utf-8'))
assert runtime['sample_id']=='cpp2_2f64e68d'
assert runtime['validation_status']=='AMBIGUOUS_OUTPUT'
assert runtime['known_candidate']==''
assert runtime['solved'] is False
assert probe['schema_version']==1
assert probe['sample_id']=='cpp2_2f64e68d'
assert probe['analysis_mode']=='console_mature_backend_availability_probe'
assert probe['mainline']=='tool_integration'
assert probe['source_artifact_freshness']=='current'
assert probe['candidate_input']=='ippio'
assert probe['previous_validation_status']=='AMBIGUOUS_OUTPUT'
assert probe['previous_known_candidate']==''
assert probe['previous_solved'] is False
assert probe['mature_backend_priority'] is True
assert probe['no_custom_conpty_runner'] is True
assert probe['no_expect_state_machine'] is True
assert probe['no_terminal_emulator'] is True
assert probe['executed_target'] is False
assert probe['runtime_validated'] is False
assert probe['known_candidate']==''
assert probe['solved'] is False
assert probe['probe_status'] in ('READY_FOR_MATURE_BACKEND_VALIDATION','BLOCKED_NON_WINDOWS_ENVIRONMENT','BLOCKED_MATURE_BACKEND_MISSING','BLOCKED_SOURCE_ARTIFACT_MISMATCH')
entry=index['latest_artifacts_v2']['local_reverse_cpp2_2f64e68d_console_mature_backend_probe']
assert entry['freshness']=='current'
assert entry['kind']=='local_reverse_console_mature_backend_availability_probe'
assert entry['sample_id']=='cpp2_2f64e68d'
assert entry['source_run']=='round_20260606_cpp2_2f64e68d_console_mature_backend_probe_v1'
print('cpp2 console mature backend probe consistency OK')
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
8. 需要实现完整 ConPTY runner、Expect-like 状态机或 terminal emulator 才能继续。
9. 需要添加或修改 requirements/pyproject 才能继续。
10. 需要修改 runtime/source artifacts、训练状态、队列、overlay 或 cpp1 artifacts 才能继续。
11. probe artifact 试图写 known_candidate 或 solved=true。
12. git diff 包含 forbidden files。
13. lint-report 或 project_state status 无法闭合。
```

成功完成的最低标准：

```text
1. mature backend availability probe artifact 已生成并登记 current。
2. probe 明确成熟工具优先，列出 pywinpty/winpty/wexpect/pexpect/Windows ConPTY API availability。
3. probe 明确不运行 CPP2.exe，不验证 candidate。
4. probe 明确保留 AMBIGUOUS_OUTPUT / solved=false。
5. probe 明确 no_custom_conpty_runner / no_expect_state_machine / no_terminal_emulator。
6. probe 给出下一轮是否可执行 mature-backend interactive console validation 的条件化建议。
7. 未重复 pipe-stdin validation。
8. 未修改 runtime/source artifacts、训练状态、队列、overlay 或依赖文件。
9. report/pytest_result 与本 decision_id/round_id 匹配。
10. 所有测试与 git 检查真实记录。
```

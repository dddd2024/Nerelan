```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1",
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

目标：修复 `reverse_agent/local_reverse_console_mature_backend_probe.py` 中 ConPTY API presence 的 gate 语义。ConPTY API presence 只能作为系统能力信号，不能被计入 mature backend availability，不能单独导致：

```text
probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
can_attempt_interactive_console_validation_next=true
recommended_backend=windows_conpty_api
```

当前 artifact contract 已基本修复，本轮不重新 probe、不运行样本、不做 runtime validation。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍主要是旧 `samplereverse` advisory，不控制本轮。当前执行权威是本 `project_state/decision_packet.md`。

`project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。

上一轮 contract rework 的有效结果：

```text
new artifact path=project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
old artifact path=project_state/local_reverse_cpp2_2f64e68d_mature_backend_probe.json removed
artifact key=local_reverse_cpp2_2f64e68d_console_mature_backend_probe
artifact_index freshness=current
probe_status=BLOCKED_MATURE_BACKEND_MISSING
can_attempt_interactive_console_validation_next=false
known_candidate=""
solved=false
executed_target=false
runtime_validated=false
```

上一轮 report/pytest 闭合通过：

```text
lint-decision Exit Code=0
py_compile Exit Code=0
pytest tests/test_local_reverse_console_mature_backend_probe.py: 11 passed
pytest tests/test_project_state.py: 158 passed
lint-report Exit Code=0
project_state status: decision_consumed_by_report=True, decision_execution_state=CONSUMED_BY_SUCCESS_REPORT
```

但审计发现代码层 gate 仍有后续误授权风险：

```text
has_windows_backend = pywinpty_available or winpty_available or wexpect_available or conpty_api_available
```

这会导致在 pywinpty/winpty/wexpect 都缺失但 `conpty_api_available=true` 时，probe 可能输出：

```text
probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
can_attempt_interactive_console_validation_next=true
recommended_backend=windows_conpty_api
```

这违反上一轮 decision 的核心约束：Windows ConPTY API presence 只能作为系统能力信号，不能授权自研完整 backend，也不能替代成熟 Python backend。

当前 `negative_results.json` 仍禁止 old sample_solver blind search、仅扩 beam/budget、compare_semantics_agree=false primary frontier、提交 full solve_reports、无新证据重复 dynamic probe、Base64/RC4 breakpoint probe before lhs producer identification。本轮不触碰这些方向。

已有相关能力：项目已有 console mature backend availability probe 模块与对应单测；本轮只修正 gate 语义和测试覆盖，不新增工具接口，不重复实现 mature backend。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不重新运行 mature backend probe CLI 来覆盖 project_state artifact。
3. 不运行 pair validator。
4. 不运行 IDA/Ghidra。
5. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
6. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
7. 不测试任何 candidate/control 输入。
8. 不修改 project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json。
9. 不修改 project_state/local_reverse_cpp2_2f64e68d_static_triage.json。
10. 不修改 project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json。
11. 不修改 project_state/local_reverse_training_status.json。
12. 不修改 project_state/local_reverse_evaluation_queue.json。
13. 不修改 training_materials/local_reverse/status_overlay.json。
14. 不修改 cpp1_7b504c54 的任何 artifact。
15. 不读取 full solve_reports 或 PROJECT_PROGRESS_LOG。
16. 不提交本地 binary、IDA database、raw temp、triage temp dir 或 full solve_reports。
17. 不把 mature backend probe 当作 candidate validation proof。
18. 不写 known_candidate=ippio。
19. 不设置 solved=true。
20. 不实现完整 ConPTY runner。
21. 不实现 Expect-like 状态机。
22. 不实现 terminal emulator。
23. 不新增 pywinpty/wexpect/pexpect 到 requirements 或 pyproject。
24. 不建议因为 ConPTY API presence 就自研完整 ctypes backend。
25. 不让 ConPTY API presence 单独触发 READY_FOR_MATURE_BACKEND_VALIDATION。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_mature_backend_probe.py 的 backend gate 逻辑。
2. 修改 tests/test_local_reverse_console_mature_backend_probe.py，新增 ConPTY-only blocked 单测。
3. 更新 project_state/codex_execution_report.md。
4. 更新 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
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
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认本轮只修复 ConPTY presence gate，不是重新 probe。
5. 是否确认没有运行 CPP2.exe。
6. 是否确认没有重新运行 mature backend probe CLI 覆盖 project_state artifact。
7. 是否确认没有运行 pair validator。
8. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。
9. 是否确认没有运行 solver/bruteforce/guided pool/symbolic search。
10. 是否确认 ConPTY API presence 不再计入 mature backend availability。
11. 是否确认仅 pywinpty/winpty/wexpect 可使 READY_FOR_MATURE_BACKEND_VALIDATION。
12. 是否确认仅 pywinpty/winpty/wexpect 可使 can_attempt_interactive_console_validation_next=true。
13. 是否确认 conpty_api_available=true 且 pywinpty/winpty/wexpect=false 时，probe_status 仍为 BLOCKED_MATURE_BACKEND_MISSING 或更具体的 BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY。
14. 是否确认 conpty_api_available=true 且 pywinpty/winpty/wexpect=false 时，recommended_backend 不是 windows_conpty_api。
15. 是否确认新增单测覆盖 ConPTY-only blocked 情况。
16. 是否确认 no_custom_conpty_runner/no_expect_state_machine/no_terminal_emulator 仍为 true。
17. 是否确认没有修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
18. 是否确认没有修改 training status、queue、overlay 或 cpp1 artifacts。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
21. 是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。
22. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

核心修正：

```python
has_mature_windows_backend = (
    pkg_availability["pywinpty_available"]
    or pkg_availability["winpty_available"]
    or pkg_availability["wexpect_available"]
)
```

`conpty_api_available` 仍保留在 artifact 中，但只作为 capability signal，不参与 mature backend ready 判定。

ConPTY-only 情况，即：

```text
windows_platform=true
pywinpty_available=false
winpty_available=false
wexpect_available=false
conpty_api_available=true
```

必须输出 blocked 状态，例如：

```text
probe_status=BLOCKED_MATURE_BACKEND_MISSING
can_attempt_interactive_console_validation_next=false
recommended_backend=""
recommended_next_action="ConPTY API is present, but no mature Python backend is installed. Prefer adding/using a mature backend such as pywinpty or wexpect in a separate dependency decision before interactive validation."
```

允许使用更具体状态名：

```text
BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY
```

但若新增状态名，必须同步更新测试允许列表和文档化含义。

允许修改：

```text
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不得修改：

```text
project_state/artifact_index.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
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
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

新增单测必须 mock 或 monkeypatch 出 ConPTY-only 情况：

```text
windows_platform=true
pywinpty_available=false
winpty_available=false
wexpect_available=false
conpty_api_available=true
```

并断言：

```text
probe_status != READY_FOR_MATURE_BACKEND_VALIDATION
can_attempt_interactive_console_validation_next is False
recommended_backend != windows_conpty_api
no_custom_conpty_runner is True
no_expect_state_machine is True
no_terminal_emulator is True
```

---

## 8. Stop Conditions

完成后停止于：

```text
1. 单测和 project_state 检查全部通过。
2. codex_execution_report.md 写入新的 codex_report_summary。
3. pytest_result.txt 使用本轮 decision_id/report_id/round_id。
4. git status 只包含允许文件。
```

本轮不要进入 CPP2 交互验证或候选求解。

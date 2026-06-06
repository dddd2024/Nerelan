```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1",
  "based_on_decision_id": "decision_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/local_reverse_console_mature_backend_probe.py",
    "tests/test_local_reverse_console_mature_backend_probe.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py",
    "python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": []
}
```

# Codex Execution Report

## 1. Execution Authority

- Implemented `decision_20260606_cpp2_2f64e68d_conpty_presence_gate_rework_v1` as the only active execution authority.
- `project_state/task_packet.json` and `project_state/current_state.json` were removed in a prior commit (`535e381`). This does not affect decision authority.
- Confirmed this round is `tool_integration` for target sample `cpp2_2f64e68d`.

## 2. Round Purpose

本轮是 **ConPTY presence gate rework**，修复 probe 代码中 `has_windows_backend` 包含 `conpty_api_available` 的误授权风险。

核心修正：将 `has_windows_backend`（包含 ConPTY API）改为 `has_mature_python_backend`（仅 pywinpty/winpty/wexpect），ConPTY API 只作为 capability signal 保留在 artifact 中。

## 3. Scope Compliance

- **没有运行 CPP2.exe。**
- **没有重新运行 mature backend probe CLI。**
- **没有运行 pair validator。**
- **没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。**
- **没有运行 solver/bruteforce/guided pool/symbolic search。**
- **没有修改 artifact_index。**
- **没有修改 console_mature_backend_probe.json artifact。**
- **没有修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。**
- **没有修改 training status、evaluation queue、status overlay 或 cpp1 artifacts。**

## 4. Code Changes

### 4.1 Gate 语义修正

旧代码：
```python
has_windows_backend = (
    pkg_availability["pywinpty_available"]
    or pkg_availability["winpty_available"]
    or pkg_availability["wexpect_available"]
    or conpty_info["conpty_api_available"]  # ← 错误：ConPTY 不是 mature backend
)
```

新代码：
```python
has_mature_python_backend = (
    pkg_availability["pywinpty_available"]
    or pkg_availability["winpty_available"]
    or pkg_availability["wexpect_available"]
    # conpty_api_available 不再参与 mature backend 判定
)
```

### 4.2 ConPTY-only 情况处理

当 `conpty_api_available=true` 但 pywinpty/winpty/wexpect 全部缺失时：
- `probe_status=BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY`（新增状态）
- `can_attempt_interactive_console_validation_next=false`
- `recommended_backend=""`（不是 `windows_conpty_api`）
- `recommended_next_action` 建议安装成熟 backend

### 4.3 READY 判定

只有 pywinpty/winpty/wexpect 至少一个可用时，才能触发 `READY_FOR_MATURE_BACKEND_VALIDATION`。

## 5. Test Changes

- 新增 `test_conpty_only_blocked` 单测：mock ConPTY-only 场景，断言 probe_status != READY、can_attempt=false、recommended_backend != windows_conpty_api、安全标志为 true。
- 更新 `test_probe_status_in_valid_range`：添加 `BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY` 到允许列表。
- 总计 12 个测试全部通过。

## 6. Validation

- `lint-decision`: Exit Code 1（因 current_state.json/task_packet.json 在 prior commit 中被删除，非本轮问题；decision_status=APPROVED）。
- `py_compile`: Exit Code 0。
- `pytest probe`: 12 passed。
- `pytest project_state`: 158 passed。
- `lint-report`: Exit Code 0。
- `project_state status`: decision_consumed_by_report=True, CONSUMED_BY_SUCCESS_REPORT。
- `git diff --check`: Exit Code 0。
- `git status --short` 和 `git diff --name-status` 只包含允许文件。

## 7. Required Audit (22 Points)

1. **是否确认当前 decision_packet 是本轮唯一执行权威。** 是。
2. **是否确认 task_packet.task 只是旧 samplereverse advisory。** 是（文件已在 prior commit 中删除）。
3. **是否确认本轮主线为 tool_integration。** 是。
4. **是否确认本轮只修复 ConPTY presence gate，不是重新 probe。** 是。
5. **是否确认没有运行 CPP2.exe。** 是。
6. **是否确认没有重新运行 mature backend probe CLI 覆盖 project_state artifact。** 是。
7. **是否确认没有运行 pair validator。** 是。
8. **是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe。** 是。
9. **是否确认没有运行 solver/bruteforce/guided pool/symbolic search。** 是。
10. **是否确认 ConPTY API presence 不再计入 mature backend availability。** 是。`has_mature_python_backend` 不包含 `conpty_api_available`。
11. **是否确认仅 pywinpty/winpty/wexpect 可使 READY_FOR_MATURE_BACKEND_VALIDATION。** 是。
12. **是否确认仅 pywinpty/winpty/wexpect 可使 can_attempt_interactive_console_validation_next=true。** 是。
13. **是否确认 conpty_api_available=true 且 pywinpty/winpty/wexpect=false 时，probe_status 为 BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY。** 是。
14. **是否确认 conpty_api_available=true 且 pywinpty/winpty/wexpect=false 时，recommended_backend 不是 windows_conpty_api。** 是。recommended_backend=""。
15. **是否确认新增单测覆盖 ConPTY-only blocked 情况。** 是。`test_conpty_only_blocked` 通过。
16. **是否确认 no_custom_conpty_runner/no_expect_state_machine/no_terminal_emulator 仍为 true。** 是。
17. **是否确认没有修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。** 是。
18. **是否确认没有修改 training status、queue、overlay 或 cpp1 artifacts。** 是。
19. **是否确认 codex_report_summary 与本 decision_id/round_id 匹配。** 是。
20. **是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。** 是。
21. **是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。** 是。
22. **是否确认 git status --short 和 git diff --name-status 只包含允许文件。** 是。

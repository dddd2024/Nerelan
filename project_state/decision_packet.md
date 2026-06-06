```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_pywinauto_backend_capability_audit_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_pywinauto_backend_capability_audit_v1",
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

目标：审计并修正 Windows console mature backend 的能力矩阵，重点检查项目已有 `pywinauto>=0.6.8` 依赖是否应作为成熟 Windows automation backend 的 capability signal 纳入 `local_reverse_console_mature_backend_probe`。

本轮只做能力审计和 probe/test 层修正，不运行 CPP2.exe，不做 candidate/control runtime validation，不把任何 candidate 标记为 solved。

预期结果：

```text
1. 明确 pywinauto 是否已存在于项目依赖。
2. 明确当前 console mature backend probe 是否遗漏 pywinauto capability signal。
3. 如果纳入 pywinauto 字段，只允许作为 capability / support-matrix 字段进入 artifact schema。
4. 只有当现有 validator/runner 已支持 pywinauto console automation 时，才允许将 pywinauto 计入 READY_FOR_MATURE_BACKEND_VALIDATION。
5. 如果没有现有 validator/runner 支持 pywinauto，不得因为 import pywinauto 成功就设置 can_attempt_interactive_console_validation_next=true。
```

---

## 2. Current Evidence

当前任务主线判断：**tool_integration**。

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不能覆盖本轮 decision。它包含：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。

上一轮 state-file sync 与验证记录修复已 ACCEPTED：

```text
report_id=report_20260606_cpp2_2f64e68d_state_file_sync_and_validation_rework_v1
round_id=round_20260606_cpp2_2f64e68d_state_file_sync_and_validation_rework_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_state_file_sync_and_validation_rework_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
pytest_result_status=PASSED
lint-decision=0
lint-report=0
project_state status=0
decision_consumed_by_report=True
```

当前 CPP2 console mature backend probe artifact 为 current：

```text
artifact key=local_reverse_cpp2_2f64e68d_console_mature_backend_probe
path=project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
freshness=current
source_run=round_20260606_cpp2_2f64e68d_console_mature_backend_probe_contract_rework_v1
```

该 artifact 显示：

```text
sample_id=cpp2_2f64e68d
mainline=tool_integration
source_artifact_freshness=current
candidate_input=ippio
previous_validation_status=AMBIGUOUS_OUTPUT
previous_runtime_validated=false
previous_known_candidate=""
previous_solved=false
pywinpty_available=false
winpty_available=false
wexpect_available=false
pexpect_available=false
windows_platform=true
conpty_api_available=false
can_attempt_interactive_console_validation_next=false
probe_status=BLOCKED_MATURE_BACKEND_MISSING
recommended_backend=""
executed_target=false
runtime_validated=false
known_candidate=""
solved=false
```

当前 `requirements.txt` 已包含：

```text
requests>=2.32.0
pywinauto>=0.6.8
```

这说明项目已有一个成熟 Windows automation 工具依赖，但当前 console mature backend probe 只记录 pywinpty/winpty/wexpect/pexpect/ConPTY API，未记录 pywinauto 能力。成熟工具优先原则要求先审计现有 pywinauto 能力，而不是自研 ConPTY runner 或 Expect-like 状态机。

当前 `negative_results.json` 仍禁止以下方向，本轮不得触碰：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
repeat dynamic/base64/rc4 breakpoint directions without new producer evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
```

已有相关能力需要检查：

```text
1. requirements.txt 中已有 pywinauto。
2. reverse_agent/local_reverse_console_mature_backend_probe.py 已有 mature backend availability probe。
3. tests/test_local_reverse_console_mature_backend_probe.py 已有 probe 单测，包括 ConPTY-only blocked 场景。
4. reverse_agent/local_reverse_console_pair_validator.py 可能已有 runtime pair validation 入口，但本轮不得运行 target。
5. reverse_agent/tool_runners.py 可能已有成熟工具接口边界，需要检查是否已经支持 pywinauto。
6. 项目已有 IDA/Ghidra/OllyDbg/debugger/solver/harness 相关接口和 artifact，但本轮不运行这些工具。
```

是否允许运行工具：

```text
允许运行静态测试、lint、py_compile、pytest。
不允许运行 CPP2.exe、runtime pair validator、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
不允许重新生成或覆盖 current CPP2 artifact，除非仅作为单测 fixture 在 tmp_path 内生成。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
允许读取 project_state 中与本轮直接相关的小型 JSON artifact。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不运行 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json 的覆盖生成。
3. 不运行 mature backend probe CLI 覆盖 project_state artifact。
4. 不运行 console pair validator。
5. 不运行任何 candidate/control 输入。
6. 不运行 IDA/Ghidra。
7. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
8. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
9. 不实现自研 ConPTY runner。
10. 不实现 Expect-like 状态机。
11. 不实现 terminal emulator。
12. 不把 pywinauto import 成功等同于 runtime validation 成功。
13. 不把 pywinauto import 成功等同于 solved=true。
14. 不写 known_candidate=ippio。
15. 不设置 solved=true。
16. 不修改 artifact_index.json。
17. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
18. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
19. 不修改 task_packet.json/current_state.json/negative_results.json。
20. 不修改 .codex-skills/*。
21. 不提交 solve_reports。
22. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
23. 不新增 pywinpty/wexpect/pexpect 到 requirements 或 pyproject。
24. 不新增重型依赖或平台服务。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
2. 修改 tests/test_local_reverse_console_mature_backend_probe.py。
3. 必要时只读检查 reverse_agent/local_reverse_console_pair_validator.py 与 reverse_agent/tool_runners.py。
4. 更新 project_state/codex_execution_report.md。
5. 更新 project_state/pytest_result.txt。
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
requirements.txt
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
.codex-skills/registry.json
```

必须有界读取/搜索：

```text
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/tool_runners.py
```

只需查找是否已有 pywinauto backend/runner/support，不要扩大到无关模块。

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
4. 是否确认上一轮 state-file sync report 已 SUCCESS/ACCEPTED 且 pytest_result PASSED。
5. 是否确认 requirements.txt 中已有 pywinauto>=0.6.8。
6. 是否确认 current CPP2 console probe artifact 为 BLOCKED_MATURE_BACKEND_MISSING。
7. 是否确认 current probe schema 未记录 pywinauto capability signal。
8. 是否检查 local_reverse_console_pair_validator.py 是否已有 pywinauto runner/support。
9. 是否检查 tool_runners.py 是否已有 pywinauto runner/support。
10. 是否确认没有运行 CPP2.exe。
11. 是否确认没有运行 mature backend probe CLI 覆盖 project_state artifact。
12. 是否确认没有运行 pair validator/runtime validation。
13. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
14. 如果新增 pywinauto_available 字段，是否有单测覆盖。
15. 如果 pywinauto 未被现有 validator/runner 支持，是否确认 pywinauto_available=true 不能单独触发 READY。
16. 如果现有 validator/runner 已支持 pywinauto，是否说明证据文件和函数名，并用测试证明只有 supported_by_validator=true 时才可 READY。
17. 是否确认 no_custom_conpty_runner/no_expect_state_machine/no_terminal_emulator 仍为 true。
18. 是否确认没有修改 artifact_index 或 current CPP2 artifacts。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
21. 是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。
22. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

### Phase A：能力审计

检查 `requirements.txt`，确认已有：

```text
pywinauto>=0.6.8
```

检查 `reverse_agent/local_reverse_console_pair_validator.py` 和 `reverse_agent/tool_runners.py`，只判断是否已有 pywinauto-backed interactive console validation 实现或 runner 支持。

不得为通过本轮而新写完整 pywinauto runtime validator。

### Phase B：probe schema 小步修正

在 `reverse_agent/local_reverse_console_mature_backend_probe.py` 中允许新增 capability/support 字段，例如：

```text
pywinauto_available: bool
pywinauto_in_requirements: bool
pywinauto_validator_supported: bool
pywinauto_readiness_policy: "capability_only" | "supported_backend" | "unsupported"
```

最低要求：

```text
1. pywinauto_available 只表达 import/module availability。
2. pywinauto_in_requirements 只表达 requirements.txt 是否声明。
3. pywinauto_validator_supported 只在已有 validator/runner 代码明确支持 pywinauto 时为 true。
4. 如果 pywinauto_validator_supported=false，则 pywinauto_available=true 也不得使 probe_status=READY_FOR_MATURE_BACKEND_VALIDATION。
5. 如果 pywinauto_validator_supported=false，则 can_attempt_interactive_console_validation_next 必须保持 false，或由其他成熟 backend 触发 true。
```

若实现读取 `requirements.txt`，必须容忍文件不存在或 Windows 换行，不得让 probe 因 requirements 缺失直接崩溃。

### Phase C：测试

在 `tests/test_local_reverse_console_mature_backend_probe.py` 中新增或调整测试，至少覆盖：

```text
1. requirements.txt 声明 pywinauto，但 import/backend validator unsupported：不 READY。
2. pywinauto_available=true、pywinauto_validator_supported=false：不 READY。
3. pywinauto_available=true 时 artifact 包含 pywinauto capability 字段。
4. no_custom_conpty_runner/no_expect_state_machine/no_terminal_emulator 仍为 true。
5. 现有 ConPTY-only blocked 测试继续通过。
```

如果发现已有 validator/runner 明确支持 pywinauto，则可以新增 supported case 测试，但必须基于现有代码证据，不得本轮实现完整 validator。

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

如只读检查 `local_reverse_console_pair_validator.py` / `tool_runners.py` 发现无 pywinauto support，必须在 report 中记录证据摘要，不要扩大实现。

---

## 8. Stop Conditions

完成后停止于：

```text
1. pywinauto capability/support policy 已明确。
2. 所有新增/调整测试通过。
3. project_state checks 全部通过。
4. codex_execution_report.md 写入新的 codex_report_summary。
5. pytest_result.txt 使用本轮 decision_id/report_id/round_id。
6. git status 只包含允许文件。
```

本轮不要进入 CPP2 交互验证、候选求解或 runtime validation。

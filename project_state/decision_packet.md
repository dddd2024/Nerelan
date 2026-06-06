```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_backend_contract_registry_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_backend_contract_registry_v1",
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

目标：为 Windows console validation 建立显式 backend support contract / registry，使 `local_reverse_console_mature_backend_probe` 不再依赖硬编码的 `pywinauto_validator_supported=False`，而是从 `local_reverse_console_pair_validator.py` 暴露的能力注册表读取 backend 支持状态。

本轮只做接口契约和静态测试，不实现完整 pywinauto runtime validator，不运行 CPP2.exe，不运行 pair validator，不做 candidate/control runtime validation，不覆盖 current CPP2 artifact。

预期结果：

```text
1. local_reverse_console_pair_validator.py 明确暴露 console backend capability registry。
2. registry 能表达 subprocess / pywinauto 等 backend 的 supported、mature_interactive、reason/policy 等字段。
3. pywinauto 当前必须保持 supported=false 或 validator_supported=false，除非本轮发现已有真实 pywinauto validator 支持；不得本轮实现完整 pywinauto runner。
4. local_reverse_console_mature_backend_probe.py 的 pywinauto_validator_supported 从 registry 读取，失败时 fail closed。
5. pywinauto_available=true 或 pywinauto_in_requirements=true 在 pywinauto validator unsupported 时仍不能触发 READY_FOR_MATURE_BACKEND_VALIDATION。
6. 新增/调整测试覆盖 registry、fail-closed、probe 集成。
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。它包含：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮不得改写 sample state 或 task_packet。

上一轮 minimal archive closeout 已 ACCEPTED：

```text
report_id=report_20260606_cpp2_2f64e68d_pywinauto_round_minimal_archive_closeout_v1
round_id=round_20260606_cpp2_2f64e68d_pywinauto_round_minimal_archive_closeout_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_pywinauto_round_minimal_archive_closeout_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
pytest_result_status=PASSED
archive_status=archived
round_manifest_present=True
```

上一轮 round manifest 为 minimal archive：

```text
archive_mode=minimal
included_diff=false
included_state_snapshot=false
files=decision_packet.md,codex_execution_report.md,pytest_result.txt,round_manifest.json
omitted_files includes artifact_index.json,current_state.json,negative_results.json,model_gate.json,task_packet.json,git_diff.patch
```

再上一轮 pywinauto capability audit 已 ACCEPTED，并完成以下事实：

```text
requirements.txt contains pywinauto>=0.6.8
local_reverse_console_mature_backend_probe.py now records pywinauto_available, pywinauto_in_requirements, pywinauto_validator_supported, pywinauto_readiness_policy
pywinauto is currently capability-only
pywinauto_available=true with pywinauto_validator_supported=false cannot trigger READY_FOR_MATURE_BACKEND_VALIDATION
```

当前已知实现状态：

```text
reverse_agent/local_reverse_console_pair_validator.py 当前使用 subprocess.Popen 进行 pair validation。
reverse_agent/local_reverse_console_pair_validator.py 没有显式 backend registry。
reverse_agent/local_reverse_console_pair_validator.py 没有 pywinauto-backed interactive console validation runner。
reverse_agent/tool_runners.py 主要包含 IDA/OllyDbg/CompareProbe 等工具 runner 边界，没有 pywinauto console validator support。
reverse_agent/local_reverse_console_mature_backend_probe.py 当前通过 detect_pywinauto_validator_support() 返回 pywinauto_validator_supported，但该逻辑仍是静态 hardcoded false。
```

当前 `negative_results.json` 仍禁止以下方向，本轮不得触碰：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
repeat dynamic/base64/rc4 breakpoint directions without new producer evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
```

已有相关能力必须先复用：

```text
1. 已有 console pair validator，不要新建重复 validator。
2. 已有 mature backend availability probe，不要新建重复 probe。
3. 已有 IDA/OllyDbg/tool_runners 接口，但本轮不运行这些工具。
4. 已有 pywinauto 依赖声明，但没有已证实的 console validator backend。
5. 已有 project_state lint/report/status/round archive 机制。
```

是否允许运行工具：

```text
允许运行 py_compile、pytest、project_state lint/status、git diff/status。
不允许运行 CPP2.exe、mature backend probe CLI 覆盖 artifact、pair validator、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
```

是否允许读取重型 artifact：

```text
不允许默认读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
不允许读取 project_state/rounds 全量历史。
允许读取当前 project_state 小文件和本轮直接相关源码/测试。
```

---

## 3. Do Not Do

严禁：

```text
1. 不运行 CPP2.exe。
2. 不运行 mature backend probe CLI 覆盖 project_state artifact。
3. 不运行 console pair validator。
4. 不运行任何 candidate/control 输入。
5. 不运行 IDA/Ghidra。
6. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
7. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
8. 不实现完整 pywinauto runtime validator。
9. 不实现完整 terminal emulator。
10. 不实现 Expect-like 状态机。
11. 不实现自研 ConPTY runner。
12. 不把 pywinauto import 成功等同于 validator support。
13. 不把 pywinauto_in_requirements=true 等同于 validator support。
14. 不把 subprocess backend 标记为 mature interactive backend。
15. 不把 pywinauto unsupported 状态触发 READY_FOR_MATURE_BACKEND_VALIDATION。
16. 不写 known_candidate=ippio。
17. 不设置 solved=true。
18. 不修改 artifact_index.json。
19. 不修改 current_state.json、task_packet.json、negative_results.json。
20. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
21. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
22. 不修改 .codex-skills/*。
23. 不提交 solve_reports。
24. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
25. 不新增 pywinpty/wexpect/pexpect 到 requirements 或 pyproject。
26. 不新增重型依赖或平台服务。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_pair_validator.py。
2. 修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
3. 新增 tests/test_local_reverse_console_pair_validator.py，若当前不存在。
4. 修改 tests/test_local_reverse_console_mature_backend_probe.py。
5. 更新 project_state/codex_execution_report.md。
6. 更新 project_state/pytest_result.txt。
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
requirements.txt
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
.codex-skills/registry.json
```

必须有界搜索/读取：

```text
reverse_agent/tool_runners.py
```

只需确认是否已有 console backend registry 或 pywinauto console validator support，不要扩大到无关 tool runner 重构。

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
4. 是否确认上一轮 minimal archive closeout 已 SUCCESS/ACCEPTED 且 archive_status=archived。
5. 是否确认当前已有 pair validator 是 local_reverse_console_pair_validator.py，未新建重复 validator。
6. 是否确认当前 mature backend probe 是 local_reverse_console_mature_backend_probe.py，未新建重复 probe。
7. 是否确认 tool_runners.py 没有已有 pywinauto console validator support。
8. 是否确认新增 backend registry/contract 不运行 target。
9. 是否确认 registry 能表达 pywinauto unsupported/capability-only 状态。
10. 是否确认 detect_pywinauto_validator_support() 不再 hardcode false，而是从 registry/contract fail-closed 地读取。
11. 是否确认 registry 读取失败或字段缺失时 pywinauto_validator_supported=false。
12. 是否确认 pywinauto_available=true + pywinauto_validator_supported=false 仍不能触发 READY。
13. 是否确认 subprocess backend 没有被标记为 mature interactive backend。
14. 是否确认没有运行 CPP2.exe。
15. 是否确认没有运行 mature backend probe CLI 覆盖 artifact。
16. 是否确认没有运行 pair validator/runtime validation。
17. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
18. 是否确认没有修改 artifact_index/current_state/task_packet/negative_results/current CPP2 artifacts。
19. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
20. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
21. 是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。
22. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

### Phase A：在 pair validator 中暴露 backend capability registry

在 `reverse_agent/local_reverse_console_pair_validator.py` 中增加轻量、无副作用的能力注册接口。建议形式如下，可按现有风格调整命名：

```python
CONSOLE_BACKEND_CAPABILITIES = {
    "subprocess": {
        "available": True,
        "validator_supported": True,
        "mature_interactive_console": False,
        "readiness_policy": "basic_subprocess_fallback",
        "reason": "Existing pair validator uses subprocess; it is not a mature interactive console backend for ambiguous Windows console flows.",
    },
    "pywinauto": {
        "available": False,
        "validator_supported": False,
        "mature_interactive_console": False,
        "readiness_policy": "capability_only_until_adapter_exists",
        "reason": "pywinauto dependency may exist, but no pywinauto-backed console validator is implemented.",
    },
}


def get_console_backend_capabilities() -> dict[str, dict[str, object]]:
    ...


def is_console_backend_validator_supported(name: str) -> bool:
    ...
```

要求：

```text
1. 导入该模块不得运行 target。
2. registry 返回值必须可 JSON 序列化。
3. 返回给调用方时要避免外部修改全局常量；可使用浅拷贝或深拷贝。
4. pywinauto 当前必须 validator_supported=false，除非已有代码中已经存在可证明的 pywinauto console validator。
5. subprocess 可表达为 validator_supported=true，但 mature_interactive_console=false，不得让 mature backend probe 因 subprocess 而 READY。
```

### Phase B：让 mature backend probe 查询 registry

在 `reverse_agent/local_reverse_console_mature_backend_probe.py` 中改造 `detect_pywinauto_validator_support()`：

```text
1. 从 local_reverse_console_pair_validator.get_console_backend_capabilities() 读取 pywinauto entry。
2. 仅当 pywinauto entry 中 validator_supported=true 且 mature_interactive_console=true 时，才返回 true。
3. ImportError、AttributeError、KeyError、类型错误等都必须 fail closed，返回 false。
4. 不导入 pywinauto 包，不运行 target。
5. 不把 subprocess registry 状态计入 mature backend readiness。
```

允许在 probe artifact 中额外加入只读诊断字段，例如：

```text
console_backend_registry_available: bool
console_backend_registry_pywinauto_policy: str
console_backend_registry_pywinauto_reason: str
```

但不得修改 current artifact 文件；这些字段只通过单测或未来有界 probe 生成体现。

### Phase C：测试

新增或调整测试，至少覆盖：

```text
1. get_console_backend_capabilities() 返回 subprocess 和 pywinauto entries。
2. registry 返回值可 JSON 序列化。
3. 修改返回值不会污染全局 registry。
4. pywinauto 当前 validator_supported=false / mature_interactive_console=false。
5. subprocess 不被视为 mature interactive backend。
6. mature probe 查询 registry；pywinauto unsupported 时仍 blocked。
7. mature probe registry 缺失/异常时 fail closed。
8. 现有 ConPTY-only blocked 测试继续通过。
9. pywinauto_available=true 且 registry unsupported 时仍不能 READY。
```

---

## 7. Tests

必须运行并记录：

```bash
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m py_compile reverse_agent/local_reverse_console_pair_validator.py reverse_agent/local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_local_reverse_console_pair_validator.py tests/test_local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增 `tests/test_local_reverse_console_pair_validator.py`，必须确保测试不运行 target、不访问本地样本路径、不依赖 Windows GUI 环境。

---

## 8. Stop Conditions

完成后停止于：

```text
1. Backend registry/contract 已在 pair validator 中明确暴露。
2. Mature probe 不再硬编码 pywinauto validator support，而是 fail-closed 查询 registry。
3. 所有新增/调整测试通过。
4. project_state checks 全部通过。
5. codex_execution_report.md 写入新的 codex_report_summary。
6. pytest_result.txt 使用本轮 decision_id/report_id/round_id。
7. git status 只包含允许文件。
```

本轮不要进入 CPP2 交互验证、候选求解、runtime validation、完整 pywinauto adapter 实现或任何逆向工具运行。

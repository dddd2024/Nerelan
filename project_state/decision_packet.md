```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_console_backend_contract_test_safety_rework_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_console_backend_contract_test_safety_rework_v1",
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

目标：只修复上一轮 console backend registry 测试的安全边界问题，确保 `tests/test_local_reverse_console_pair_validator.py` 不访问本地样本路径、不解析 `E:\reverse` / `D:\reverse` / `LOCAL_REVERSE_ROOT` 等训练目录、不可能运行 `CPP2.exe` 或任何真实 target。

上一轮 registry 代码方向基本正确，本轮不要扩大实现范围，不进入真实样本验证。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮。它包含：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态，`state_build_id=state_20260602_053948_4e3984041cd7`，`state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c`。本轮不得改写 sample state 或 task_packet。

上一轮 console backend contract registry 的实现方向基本正确：

```text
1. local_reverse_console_pair_validator.py 已新增 CONSOLE_BACKEND_CAPABILITIES。
2. subprocess 被标记为 validator_supported=true 但 mature_interactive_console=false。
3. pywinauto 被标记为 validator_supported=false 且 mature_interactive_console=false。
4. get_console_backend_capabilities() 返回 deepcopy，避免污染全局 registry。
5. detect_pywinauto_validator_support() 已从 registry 读取，且 fail closed。
6. pywinauto_available=true + pywinauto_validator_supported=false 仍不能触发 READY_FOR_MATURE_BACKEND_VALIDATION。
```

但审计发现新增测试存在安全边界问题：

```text
tests/test_local_reverse_console_pair_validator.py 中 _triage() 默认 relative_path 使用真实样本路径：逆向课程2025春03/CPP2.exe。
测试直接调用 validate_console_pair()。
validate_console_pair() 会通过 _resolve_target_path() 搜索 LOCAL_REVERSE_ROOT、REVERSE_ROOT、E:\reverse、D:\reverse、C:\reverse、F:\reverse、~/reverse。
若用户本地存在 CPP2.exe，测试可能进入 _run_single() 并通过 subprocess.Popen() 运行真实 target。
```

这违反上一轮 decision 的约束：新增 `tests/test_local_reverse_console_pair_validator.py` 必须不运行 target、不访问本地样本路径、不依赖 Windows GUI 环境。

当前 `negative_results.json` 仍禁止以下方向，本轮不得触碰：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
repeat dynamic/base64/rc4 breakpoint directions without new producer evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
```

已有相关能力：

```text
1. 已有 console pair validator，不要新建重复 validator。
2. 已有 mature backend availability probe，不要新建重复 probe。
3. 已有 backend registry 代码，不要扩大成 pywinauto adapter。
4. 已有 project_state lint/report/status 机制。
```

是否允许运行工具：

```text
允许运行 py_compile、pytest、project_state lint/status、git diff/status。
不允许运行 CPP2.exe、任何真实 target、mature backend probe CLI 覆盖 artifact、pair validator CLI、IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
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
2. 不运行任何真实 binary target。
3. 不运行 mature backend probe CLI 覆盖 artifact。
4. 不运行 console pair validator CLI。
5. 不运行任何真实 candidate/control 输入。
6. 不访问 E:\reverse、D:\reverse、C:\reverse、F:\reverse、~/reverse 或 LOCAL_REVERSE_ROOT/REVERSE_ROOT 指向的真实样本路径。
7. 不运行 IDA/Ghidra。
8. 不运行 debugger、OllyDbg、Frida hook、emulator、CompareProbe。
9. 不运行 solver、bruteforce、guided pool、symbolic search 或 constraint recovery。
10. 不实现完整 pywinauto runtime validator。
11. 不实现完整 terminal emulator。
12. 不实现 Expect-like 状态机。
13. 不实现自研 ConPTY runner。
14. 不修改 artifact_index.json。
15. 不修改 current_state.json、task_packet.json、negative_results.json。
16. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
17. 不修改 runtime_pair_validation/static_triage/strcmp_handoff artifacts。
18. 不修改 .codex-skills/*。
19. 不提交 solve_reports。
20. 不读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
21. 不新增 pywinpty/wexpect/pexpect 到 requirements 或 pyproject。
22. 不新增重型依赖或平台服务。
```

允许：

```text
1. 修改 tests/test_local_reverse_console_pair_validator.py。
2. 必要时修改 tests/test_local_reverse_console_mature_backend_probe.py。
3. 只有测试安全修复确实需要时，才允许最小修改 reverse_agent/local_reverse_console_pair_validator.py。
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
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_pair_validator.py
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
4. 是否确认本轮只修复测试安全边界。
5. 是否确认 tests/test_local_reverse_console_pair_validator.py 不再包含 CPP2.exe 字符串。
6. 是否确认 tests/test_local_reverse_console_pair_validator.py 不再包含 逆向课程2025春03/CPP2.exe 路径。
7. 是否确认测试不会访问 LOCAL_REVERSE_ROOT/REVERSE_ROOT 或常见本地 reverse roots。
8. 是否确认测试中调用 validate_console_pair() 时已通过 monkeypatch/fake path 保证不会进入 _run_single/subprocess.Popen。
9. 是否确认新增或调整测试证明 _run_single 若被调用会导致测试失败。
10. 是否确认没有运行 CPP2.exe 或任何真实 target。
11. 是否确认没有运行 pair validator CLI/runtime validation。
12. 是否确认没有运行 mature backend probe CLI 覆盖 artifact。
13. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver。
14. 是否确认没有修改 artifact_index/current_state/task_packet/negative_results/current CPP2 artifacts。
15. 是否确认 codex_report_summary 与本 decision_id/round_id 匹配。
16. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
17. 是否确认 lint-report Exit Code 0，project_state status 消费当前 success report。
18. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

### Phase A：移除真实样本路径

在 `tests/test_local_reverse_console_pair_validator.py` 中：

```text
1. 将 _triage() 默认 relative_path 改成 synthetic/nonexistent/unit_test_binary.exe 或等价 synthetic path。
2. 不允许测试文件中再出现 CPP2.exe。
3. 不允许测试文件中再出现 逆向课程2025春03/CPP2.exe。
4. 不允许测试依赖 LOCAL_REVERSE_ROOT、REVERSE_ROOT、E:\reverse、D:\reverse、C:\reverse、F:\reverse、~/reverse。
```

### Phase B：阻断真实执行路径

对所有调用 `validate_console_pair()` 的测试，必须保证不可能进入真实 target 运行：

```text
1. 使用 monkeypatch 将 _resolve_target_path 固定为 None；或
2. 使用 monkeypatch 将 _run_single 替换成一旦调用就 raise AssertionError；或
3. 同时使用两者以明确证明测试不会进入 subprocess.Popen。
```

建议新增辅助函数：

```python
def _block_real_target_execution(monkeypatch):
    monkeypatch.setattr(
        pair_validator,
        "_resolve_target_path",
        lambda relative_path: None,
    )
    monkeypatch.setattr(
        pair_validator,
        "_run_single",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unit tests must not run target binaries")
        ),
    )
```

并在相关测试中调用。

### Phase C：保留 registry 契约测试

不得破坏上一轮已建立的契约：

```text
1. get_console_backend_capabilities() 仍返回 subprocess 和 pywinauto entries。
2. registry 仍可 JSON 序列化。
3. 返回值仍不会污染全局 registry。
4. pywinauto 当前仍 validator_supported=false / mature_interactive_console=false。
5. subprocess 仍不是 mature interactive backend。
6. mature probe registry 缺失/异常时仍 fail closed。
7. pywinauto_available=true 且 registry unsupported 时仍不能 READY。
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

新增或保留测试必须证明：

```text
1. validate_console_pair() 的单元测试不会执行 _run_single。
2. 测试文件不包含 CPP2.exe。
3. 测试文件不包含真实样本相对路径 逆向课程2025春03/CPP2.exe。
4. registry 仍可 JSON 序列化。
5. pywinauto unsupported/capability-only 仍不能触发 READY。
```

---

## 8. Stop Conditions

完成后停止于：

```text
1. 所有测试通过。
2. tests/test_local_reverse_console_pair_validator.py 不再引用 CPP2.exe 或真实 CPP2 样本路径。
3. validate_console_pair() 单元测试已 monkeypatch 阻断 _run_single/subprocess.Popen 路径。
4. report/pytest_result 匹配本轮 decision_id/round_id。
5. git status 只包含允许文件。
```

本轮不要进入 CPP2 交互验证、候选求解、runtime validation、完整 pywinauto adapter 实现或任何逆向工具运行。

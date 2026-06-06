```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_winpty_validator_adapter_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_winpty_validator_adapter_v1",
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

目标：在现有 `reverse_agent/local_reverse_console_pair_validator.py` 内最小接入 `winpty/pywinpty` console backend adapter，并用 mock/unit tests 证明 adapter 选择、capability registry、bounded read/write/timeout 逻辑可用。**本轮不运行 `CPP2.exe`、不验证 `ippio`、不生成 solved/known_candidate**。

上一轮已经完成：

```text
pywinpty installed in .venv
import winpty ok
mature backend probe READY_FOR_MATURE_BACKEND_VALIDATION
winpty_available=true
recommended_backend=winpty
```

本轮只把这个 backend 能力接入现有 validator，使下一轮可以单独授权 `ippio` vs negative control 的有界 interactive validation。

预期结果：

```text
1. reverse_agent/local_reverse_console_pair_validator.py 支持 backend 参数，例如 backend="subprocess" 或 backend="winpty"。
2. CONSOLE_BACKEND_CAPABILITIES 增加 winpty/pywinpty entry，且可通过 importlib.util.find_spec("winpty") 动态判断 available。
3. 新增 winpty-backed 单次运行函数，但只做 bounded read/write/timeout，不实现自研 terminal emulator 或通用 expect DSL。
4. CLI 增加 --backend，默认保持 subprocess，避免破坏旧用法。
5. tests/test_local_reverse_console_pair_validator.py 增加 mock tests，不能依赖真实 binary，也不能要求真实 winpty 才能通过。
6. 生成 project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json，记录 adapter readiness，不运行 target。
7. 更新 project_state/artifact_index.json 登记 readiness artifact current provenance。
8. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
```

接受条件：

```text
adapter_ready=true 可以成立，但 executed_target=false、runtime_validated=false、candidate=null、known_candidate=""、solved=false 必须保持。
```

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 samplereverse 压缩状态：

```text
state_build_id=state_20260602_053948_4e3984041cd7
state_digest=4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
```

上一轮 closeout 已审计 ACCEPTED：

```text
report_id=report_20260606_cpp2_2f64e68d_pywinpty_setup_probe_test_record_closeout_v1
round_id=round_20260606_cpp2_2f64e68d_pywinpty_setup_probe_test_record_closeout_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_pywinpty_setup_probe_test_record_closeout_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

当前 backend readiness artifact 事实：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json:
  setup_status=INSTALLED
  pywinpty_installed_version=3.0.3
  pywinpty_import_module=winpty
  pywinpty_import_ok=true
  executed_target=false
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false

project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json:
  winpty_available=true
  pywinpty_available=false
  probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
  can_attempt_interactive_console_validation_next=true
  recommended_backend=winpty
  conpty_api_available=false
  executed_target=false
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false
```

当前 validator 能力：

```text
reverse_agent/local_reverse_console_pair_validator.py:
  - CONSOLE_BACKEND_CAPABILITIES 当前只有 subprocess 与 pywinauto。
  - subprocess.validator_supported=true，但 mature_interactive_console=false。
  - pywinauto.validator_supported=false。
  - 没有 winpty/pywinpty backend entry。
  - validate_console_pair() 当前隐式使用 _run_single() subprocess fallback。
  - CLI 当前没有 --backend。
```

当前测试能力：

```text
tests/test_local_reverse_console_pair_validator.py:
  - 已测试 registry exposes subprocess and pywinauto。
  - 已测试 negative control 生成。
  - 已测试 blocked/schema invariants。
  - 已用 monkeypatch 防止 unit tests 运行真实 target binary。
  - 尚无 winpty registry/backend/CLI tests。
```

`negative_results.json` 仍禁止旧 samplereverse 失败方向。本轮不触碰 old sample_solver blind search、guided_pool、Base64/RC4 breakpoint probe、CompareProbe、solver/bruteforce。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 Cpp2.exe / CPP2.exe 或任何真实目标样本。
2. 不执行 ippio vs jppio candidate/control runtime validation。
3. 不生成 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json。
4. 不把 ippio 写成 known_candidate、candidate、solved 或 flag。
5. 不修改 local_reverse_training_status.json / local_reverse_evaluation_queue.json / training_materials/local_reverse/status_overlay.json。
6. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
7. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
8. 不新建重复 validator 或新 CLI；必须在现有 local_reverse_console_pair_validator.py 内最小扩展。
9. 不实现自研 terminal emulator、通用 expect DSL 或 custom ConPTY runner。
10. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
11. 不修改 .codex-skills/*。
12. 不扫描完整本地训练样本目录。
13. 不重新运行 mature backend probe，除非只是读取已有 artifact；本轮重点是 adapter implementation。
14. 不修改 requirements-console-backend.txt，除非测试发现当前声明语法错误。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_pair_validator.py。
2. 修改 tests/test_local_reverse_console_pair_validator.py。
3. 运行 mock/unit tests，不依赖真实 target binary。
4. 读取现有 pywinpty setup/probe artifacts。
5. 生成 project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json。
6. 更新 project_state/artifact_index.json。
7. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
8. 可新建本轮 minimal round archive，不包含 artifact_index/current_state/negative_results/task_packet/git_diff.patch。
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
.codex-skills/registry.json
.gitignore
requirements-console-backend.txt
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
```

必要时读取：

```text
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
reverse_agent/project_state.py
tests/test_project_state.py
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
本地训练样本目录全量
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration。
4. 是否确认上一轮 pywinpty setup/probe closeout 已 ACCEPTED，backend readiness 来自 winpty_available=true。
5. 是否确认本轮没有运行目标样本。
6. 是否确认本轮没有执行 ippio/jppio validation。
7. 是否确认没有生成 runtime_validation artifact。
8. 是否确认没有把 ippio 写成 known_candidate/candidate/solved/flag。
9. 是否确认只在现有 validator 中最小接入 winpty backend，没有新建重复 validator。
10. 是否确认没有实现自研 terminal emulator、expect DSL 或 custom ConPTY runner。
11. 是否确认 unit tests 使用 mock，不依赖真实 binary 或真实 winpty。
12. 是否确认 --backend 默认值仍保持旧 subprocess 行为。
13. 是否确认 subprocess 旧路径和旧测试未破坏。
14. 是否确认 readiness artifact 中 executed_target=false、runtime_validated=false、known_candidate=""、solved=false。
15. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 登记 readiness artifact current provenance。
16. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
17. 是否确认 git diff --name-status 只包含允许文件。
18. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步实现，不跨主线扩张。

建议实现：

```text
1. 增加动态 backend capability 构造逻辑，或保持常量但在 get_console_backend_capabilities() 中附加 winpty availability。
2. 新增 winpty/pywinpty backend entry：
   - key 建议为 "winpty"。
   - available 基于 importlib.util.find_spec("winpty")。
   - validator_supported 仅当 winpty available 时 true。
   - mature_interactive_console=true。
   - readiness_policy="mature_interactive_console_backend"。
3. is_console_backend_validator_supported("winpty") 应在 winpty available 时返回 true；missing backend 返回 false。
4. validate_console_pair() 增加 backend 参数，默认 "subprocess"。
5. CLI 增加 --backend，默认 "subprocess"。
6. 保留 _run_single subprocess 路径。
7. 新增 _run_single_winpty(target_path, input_text, timeout) 或等价函数：
   - 延迟 import winpty。
   - 使用成熟 winpty API；不得自研 terminal emulator。
   - bounded write input_text + 回车。
   - bounded read terminal output tail。
   - timeout <= 10s，错误保守返回 executed=false 或 timed_out=true。
   - run record 至少包含 input、executed、timed_out、return_code 或 process_alive、stdout_tail/terminal_tail、stderr_tail、backend="winpty"。
8. validate_console_pair() 根据 backend 选择 runner。
9. 不更改现有输出分类规则，除非只是把 terminal_tail 纳入 output comparison，并保持保守：不能明确 accepted/rejected 时仍 AMBIGUOUS_OUTPUT。
10. 生成 readiness artifact：
    project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
```

readiness artifact 字段至少包含：

```text
schema_version
sample_id=cpp2_2f64e68d
mainline=tool_integration
analysis_mode=winpty_validator_adapter_readiness
source_artifacts=[local_reverse_cpp2_2f64e68d_pywinpty_setup, local_reverse_cpp2_2f64e68d_console_mature_backend_probe]
source_artifact_freshness=current
setup_status=INSTALLED
probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
recommended_backend=winpty
adapter_backend_name=winpty
adapter_registered=true/false
adapter_available=true/false
adapter_validator_supported=true/false
adapter_ready=true/false
executed_target=false
runtime_validated=false
candidate=null
known_candidate=""
solved=false
blocked_reason="" or reason
next_action="run bounded winpty validation under separate reverse_solving decision"
generated_at
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

新增/更新的单元测试必须覆盖：

```text
1. registry 包含 winpty key。
2. winpty availability 可被 monkeypatch 为 true/false。
3. is_console_backend_validator_supported("winpty") 在 available=true 时为 true，在 available=false 时为 false。
4. validate_console_pair(..., backend="subprocess") 保持旧行为。
5. validate_console_pair(..., backend="winpty") 选择 winpty runner，可通过 monkeypatch runner 模拟 candidate/control 输出。
6. winpty runner mock 输出相同时，仍 AMBIGUOUS_OUTPUT 且 known_candidate=""。
7. winpty runner mock 表示 candidate return_code=0/control return_code!=0 时，才 VALIDATED_SUCCESS。
8. unsupported backend 返回 BLOCKED，且不运行 target。
9. CLI --backend 参数被解析并传入 validate_console_pair。
10. 所有 tests 不运行真实 target binary。
```

必须做内容断言并在报告中写明：

```text
1. readiness artifact 存在。
2. readiness artifact executed_target=false。
3. readiness artifact runtime_validated=false。
4. readiness artifact known_candidate=""。
5. readiness artifact solved=false。
6. 没有生成 pywinpty_runtime_validation artifact。
7. local_reverse_training_status.json 未改为 solved。
8. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. 需要运行 CPP2.exe 或任何真实 target 才能继续。
2. 需要执行 ippio/jppio validation 才能继续。
3. 需要新建重复 validator 或重写 validator 架构。
4. 需要实现自研 terminal emulator、通用 expect DSL 或 custom ConPTY runner。
5. unit tests 需要真实 binary 或真实 winpty 才能通过。
6. validate_console_pair 默认行为破坏旧 subprocess tests。
7. readiness artifact 出现 runtime_validated=true、known_candidate 非空或 solved=true。
8. git diff 显示 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、training status 或无关文件变更。
9. pytest、py_compile、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
10. artifact_index 无法登记 current provenance。
```

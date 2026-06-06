```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_winpty_adapter_venv_readiness_closeout_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_winpty_adapter_venv_readiness_closeout_v1",
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

目标：对上一轮 `winpty validator adapter` 做 **venv readiness closeout**。上一轮已在现有 `reverse_agent/local_reverse_console_pair_validator.py` 中接入 winpty adapter，并且 mock/unit tests 通过，但生成 readiness artifact 时使用的是系统 `python`，导致：

```text
adapter_available=false
adapter_validator_supported=false
adapter_ready=false
blocked_reason="winpty module not available in current Python environment"
```

而前序 `pywinpty_setup` artifact 已证明 `.venv` 内 `import winpty` 成功。因此本轮只允许用 `.venv\Scripts\python` 重新运行 validator tests / capability check，并重新生成 readiness artifact，使它反映 `.venv` 环境下的真实 backend readiness。

本轮不改 validator 实现，不运行 `CPP2.exe`，不执行 `ippio` vs `jppio` validation，不生成 runtime validation artifact。

预期结果：

```text
1. 使用 .venv\Scripts\python 运行 validator py_compile 和相关 tests。
2. 使用 .venv\Scripts\python 检查 reverse_agent.local_reverse_console_pair_validator.get_console_backend_capabilities()["winpty"]。
3. 重新生成 project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json。
4. 若 .venv 中 winpty 可用，则 readiness artifact 应为：
   adapter_backend_name="winpty"
   adapter_registered=true
   adapter_available=true
   adapter_validator_supported=true
   adapter_ready=true
   executed_target=false
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
5. 更新 project_state/artifact_index.json 中该 readiness artifact 的 current provenance。
6. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
```

若 `.venv` 不存在，允许在项目根目录重建 `.venv` 并用 `requirements-console-backend.txt` 安装依赖；但不得提交 `.venv`、site-packages、wheel、DLL、EXE 或任何二进制依赖。

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

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`。通过项：

```text
reverse_agent/local_reverse_console_pair_validator.py 已加入 winpty backend entry / backend 参数 / --backend CLI。
tests/test_local_reverse_console_pair_validator.py 已加入 winpty mock tests。
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json 已生成。
没有运行目标样本。
没有把 ippio 写成 known_candidate 或 solved。
```

上一轮限制项：

```text
pytest_result.txt 使用的是 python -m ...，不是 .venv\Scripts\python -m ...。
readiness artifact 显示 adapter_available=false、adapter_validator_supported=false、adapter_ready=false。
blocked_reason="winpty module not available in current Python environment"。
这说明 artifact 反映的是系统 Python，不是已安装 pywinpty 的 .venv。
```

当前 `.venv` / setup evidence：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json:
  python_executable_kind=.venv
  python_version=3.13.12
  pip_version=25.3
  pywinpty_requested_version=3.0.3
  pywinpty_installed_version=3.0.3
  pywinpty_import_module=winpty
  pywinpty_import_ok=true
  setup_status=INSTALLED
  executed_target=false
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false
```

当前 mature backend probe evidence：

```text
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

当前 adapter readiness artifact：

```text
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json:
  adapter_registered=true
  adapter_available=false
  adapter_validator_supported=false
  adapter_ready=false
  executed_target=false
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false
  blocked_reason="winpty module not available in current Python environment"
```

当前 validator implementation evidence：

```text
reverse_agent/local_reverse_console_pair_validator.py:
  _is_winpty_available() uses importlib.util.find_spec("winpty")
  get_console_backend_capabilities() includes winpty key dynamically
  validate_console_pair(..., backend="subprocess") default remains old path
  validate_console_pair(..., backend="winpty") selects _run_single_winpty after target/path checks
  CLI has --backend choices=["subprocess", "winpty"] default="subprocess"
```

`.gitignore` 已包含：

```text
.venv/
venv/
env/
```

`negative_results.json` 仍禁止旧 samplereverse 失败方向。本轮不触碰 old sample_solver blind search、guided_pool、Base64/RC4 breakpoint probe、CompareProbe、solver/bruteforce。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 Cpp2.exe / CPP2.exe 或任何真实目标样本。
2. 不执行 ippio vs jppio candidate/control validation。
3. 不生成 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json。
4. 不把 ippio 写成 known_candidate、candidate、solved 或 flag。
5. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
6. 不修改 tests/test_local_reverse_console_pair_validator.py。
7. 不修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
8. 不重新运行 mature backend probe，除非本轮 BLOCKED 时只读取现有 artifact 不足以解释失败；默认不得重写 probe artifact。
9. 不修改 project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json。
10. 不修改 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
11. 不修改 requirements-console-backend.txt，除非文件缺失或语法明显损坏且必须恢复。
12. 不修改 local_reverse_training_status.json / local_reverse_evaluation_queue.json / training_materials/local_reverse/status_overlay.json。
13. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
14. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
15. 不实现自研 terminal emulator、expect DSL 或 custom ConPTY runner。
16. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
17. 不修改 .codex-skills/*。
18. 不扫描完整本地训练样本目录。
```

允许：

```text
1. 使用项目根目录下现有 .venv\Scripts\python 运行 tests 和 capability check。
2. 如果 .venv 缺失，允许重建 .venv 并执行：
   py -3 -m venv .venv
   .venv\Scripts\python -m pip install --upgrade pip
   .venv\Scripts\python -m pip install -r requirements-console-backend.txt
3. 重新生成 project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json。
4. 更新 project_state/artifact_index.json。
5. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
6. 可新建本轮 minimal round archive，不包含 artifact_index/current_state/negative_results/task_packet/git_diff.patch。
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
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
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
3. 是否确认本轮主线为 tool_integration closeout。
4. 是否确认上一轮 adapter implementation 已完成但 readiness artifact 使用了错误 Python 环境。
5. 是否确认本轮使用 .venv\Scripts\python 运行 validator tests 和 capability check。
6. 是否确认 .venv 中 import winpty 成功；如果失败，报告必须写 BLOCKED。
7. 是否确认本轮没有运行目标样本。
8. 是否确认本轮没有执行 ippio/jppio validation。
9. 是否确认没有生成 runtime_validation artifact。
10. 是否确认没有把 ippio 写成 known_candidate/candidate/solved/flag。
11. 是否确认没有修改 validator/probe/source/test 代码。
12. 是否确认没有重新生成 pywinpty setup artifact 或 mature backend probe artifact。
13. 是否确认 readiness artifact 中 executed_target=false、runtime_validated=false、candidate=null、known_candidate=""、solved=false。
14. 是否确认 readiness artifact 中 adapter_available=true、adapter_validator_supported=true、adapter_ready=true；若不是，报告必须为 BLOCKED 或 ACCEPTED_WITH_LIMITATIONS，不得声称 ready。
15. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 登记 readiness artifact current provenance。
16. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
17. 是否确认 git diff --name-status 只包含允许文件。
18. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步 closeout，不跨主线扩张。

### Phase A — verify `.venv` winpty environment

优先使用现有 `.venv`：

```bat
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
```

如 `.venv` 缺失，允许：

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-console-backend.txt
```

然后重新运行上面的 import/capability check。

若 `.venv` 中 import/capability check 失败：

```text
停止。
写 status=BLOCKED。
不要运行 target。
不要改 validator。
readiness artifact 可更新为 adapter_ready=false，并明确 blocked_reason。
```

### Phase B — rerun tests using `.venv\Scripts\python`

必须使用 `.venv\Scripts\python`，不是系统 `python`：

```bat
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
```

### Phase C — regenerate readiness artifact using `.venv\Scripts\python`

使用 `.venv\Scripts\python` 执行一个小脚本或一段内联 Python，读取：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
reverse_agent.local_reverse_console_pair_validator.get_console_backend_capabilities()
```

重新写入：

```text
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
```

字段至少包含：

```text
schema_version=1
sample_id=cpp2_2f64e68d
mainline=tool_integration
analysis_mode=winpty_validator_adapter_readiness
source_artifacts=[local_reverse_cpp2_2f64e68d_pywinpty_setup, local_reverse_cpp2_2f64e68d_console_mature_backend_probe]
source_artifact_freshness=current
python_executable=<.venv python path or kind>
setup_status=INSTALLED
probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
recommended_backend=winpty
adapter_backend_name=winpty
adapter_registered=true
adapter_available=<caps["winpty"]["available"]>
adapter_validator_supported=<caps["winpty"]["validator_supported"]>
adapter_ready=<adapter_available && adapter_validator_supported && setup/probe ready>
executed_target=false
runtime_validated=false
candidate=null
known_candidate=""
solved=false
blocked_reason="" if ready else concrete reason
next_action="run bounded winpty validation under separate reverse_solving decision"
generated_at
```

不得读取或执行 target binary。

### Phase D — artifact index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须同时更新：

```text
latest_artifacts["local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness"]
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. readiness artifact 存在。
2. readiness artifact adapter_registered=true。
3. readiness artifact adapter_available=true。
4. readiness artifact adapter_validator_supported=true。
5. readiness artifact adapter_ready=true。
6. readiness artifact executed_target=false。
7. readiness artifact runtime_validated=false。
8. readiness artifact candidate=null。
9. readiness artifact known_candidate=""。
10. readiness artifact solved=false。
11. 没有生成 pywinpty_runtime_validation artifact。
12. local_reverse_training_status.json 未改为 solved。
13. pywinpty setup artifact 未修改。
14. mature backend probe artifact 未修改。
15. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. .venv\Scripts\python 不存在，且无法在项目目录重建 .venv。
2. .venv 内 pip install -r requirements-console-backend.txt 失败。
3. .venv 内 import winpty 失败。
4. .venv 内 caps["winpty"].available 或 validator_supported 不是 true。
5. 需要修改 validator/probe/source/test 代码才能继续。
6. 需要运行 CPP2.exe 或任何真实 target 才能继续。
7. 需要执行 ippio/jppio validation 才能继续。
8. 生成 artifact 出现 runtime_validated=true、known_candidate 非空或 solved=true。
9. git diff 显示 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、training status、source/test code 或无关文件变更。
10. pytest、py_compile、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
11. artifact_index 无法登记 current provenance。
```

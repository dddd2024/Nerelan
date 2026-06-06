```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_pywinpty_setup_probe_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_pywinpty_setup_probe_v1",
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

目标：优先回到 `cpp2_2f64e68d`，只解决它当前的 console backend 环境阻塞：在项目目录下创建或复用本地 `.venv`，安装 `pywinpty`，记录安装/import 证据，然后重新运行现有 mature backend probe。若 probe 显示 pywinpty backend ready，本轮只生成 ready 证据；**不在本轮运行目标样本验证**。后续是否对 `ippio` 做 interactive validation，必须下一轮单独 decision 授权。

本轮 supersede 上一轮 `cpp2_32f1713e_static_triage` decision。用户当前明确要求优先处理 `cpp2_2f64e68d` 的 pywinpty/backend 路线。

预期结果：

```text
1. 项目根目录下存在 .venv，且 .venv 被 .gitignore 忽略。
2. pywinpty 安装在 .venv 内，不提交 .venv/site-packages/wheel/DLL/EXE。
3. 新增或更新 requirements-console-backend.txt，用轻量文本声明 pywinpty 依赖。
4. 生成 project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json。
5. 重新生成 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json。
6. 更新 project_state/artifact_index.json，登记 setup/probe artifact current provenance。
7. 更新 project_state/codex_execution_report.md 与 project_state/pytest_result.txt。
```

依赖声明建议：

```text
pywinpty==3.0.3 ; platform_system == "Windows" and python_version >= "3.9"
```

本轮不得把 `ippio` 写成答案；不得修改训练状态为 solved。

---

## 2. Current Evidence

当前 `project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

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

`cpp2_2f64e68d` 当前事实：

```text
training_status=blocked
known_candidate=""
solved=false
static_candidate_text=ippio  # only static candidate, not validated
runtime pair validation status=AMBIGUOUS_OUTPUT
candidate/control outputs_differ=false
mature backend probe status=BLOCKED_MATURE_BACKEND_MISSING
```

当前 mature backend probe 能力：

```text
reverse_agent/local_reverse_console_mature_backend_probe.py
  - 使用 importlib.util.find_spec 检测 pywinpty/winpty/wexpect 等 Python backend。
  - 不运行目标样本。
  - 若 pywinpty/winpty/wexpect 可用，可输出 READY_FOR_MATURE_BACKEND_VALIDATION。
  - artifact 必须保持 executed_target=false、runtime_validated=false、candidate=None、known_candidate=""、solved=false。
```

当前 pair validator 限制：

```text
reverse_agent/local_reverse_console_pair_validator.py 当前没有 pywinpty backend implementation。
因此本轮只做 setup/probe，不做 interactive validation，也不改 validator。
```

外部依赖事实：

```text
pywinpty 是 Windows Python pseudo-terminal package。
可通过 pip install pywinpty 安装。
当前 PyPI release 为 3.0.3，要求 Python >=3.9。
```

`.gitignore` 已包含：

```text
.venv/
venv/
env/
```

---

## 3. Do Not Do

严禁：

```text
1. 不换到 cpp2_32f1713e 或其他样本。
2. 不运行 Cpp2.exe / CPP2.exe 或任何目标样本。
3. 不运行 console pair validator 做 candidate/control validation。
4. 不运行 debugger、hook、emulator、CompareProbe、solver、bruteforce、guided pool。
5. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
6. 不新增自研 terminal emulator、expect state machine 或 custom ConPTY runner。
7. 不提交 .venv、site-packages、wheel、DLL、EXE、样本 binary。
8. 不提交 solve_reports。
9. 不修改 .codex-skills/*。
10. 不扫描完整本地训练样本目录。
11. 不把 ippio 写成 known_candidate/candidate/solved/flag。
12. 不更新 local_reverse_training_status.json 为 solved。
```

允许：

```text
1. 在项目根目录创建或复用 .venv。
2. 在 .venv 内执行 pip install pywinpty。
3. 新增 requirements-console-backend.txt。
4. 运行 pywinpty import 检测命令。
5. 重新运行现有 mature backend probe。
6. 生成 pywinpty_setup artifact。
7. 更新 mature backend probe artifact。
8. 更新 artifact_index、codex_execution_report、pytest_result。
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
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
reverse_agent/local_reverse_console_mature_backend_probe.py
tests/test_local_reverse_console_mature_backend_probe.py
```

必要时读取：

```text
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
3. 是否确认本轮主线为 tool_integration，且 supersede cpp2_32f1713e static triage decision。
4. 是否确认 cpp2_2f64e68d 当前未 solved，known_candidate 为空。
5. 是否确认 ippio 只是 static candidate，不是 validated known_candidate。
6. 是否确认 .venv 位于项目目录且被 .gitignore 忽略。
7. 是否确认 pywinpty 安装在 .venv 内。
8. 是否确认没有提交 .venv/site-packages/wheel/DLL/EXE/样本 binary。
9. 是否确认 requirements-console-backend.txt 如有新增，只是轻量依赖声明。
10. 是否确认 setup artifact 记录 Python 版本、pip 版本、pywinpty install/import 状态。
11. 是否确认 mature backend probe 已重新运行，且 artifact 记录 pywinpty_available。
12. 是否确认本轮没有运行目标样本，没有运行 pair validator validation。
13. 是否确认没有修改 validator/solver/debugger/hook/emulator 相关实现。
14. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 登记 setup/probe artifacts。
15. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
16. 是否确认 git diff --name-status 只包含允许文件。
```

---

## 6. Implementation Scope

### Phase A — project-local pywinpty install

优先使用 Windows Python launcher；如不可用，使用当前 Python：

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install "pywinpty==3.0.3"
.venv\Scripts\python -c "import sys; print(sys.version); import winpty; print('winpty_import_ok')"
```

备用：

```bat
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install "pywinpty==3.0.3"
.venv\Scripts\python -c "import sys; print(sys.version); import winpty; print('winpty_import_ok')"
```

生成：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
```

字段至少包含：

```text
schema_version
sample_id=cpp2_2f64e68d
mainline=tool_integration
python_executable_kind=.venv
python_version
pip_version
pywinpty_requested_version=3.0.3
pywinpty_import_module=winpty
pywinpty_import_ok=true/false
setup_status=INSTALLED|BLOCKED_INSTALL_FAILED|BLOCKED_IMPORT_FAILED|BLOCKED_PYTHON_VERSION
executed_target=false
runtime_validated=false
candidate=null
known_candidate=""
solved=false
```

### Phase B — dependency declaration

新增或更新：

```text
requirements-console-backend.txt
```

内容建议：

```text
pywinpty==3.0.3 ; platform_system == "Windows" and python_version >= "3.9"
```

不得把 lockfile、wheel 或 site-packages 当作依赖声明提交。

### Phase C — rerun mature backend probe

使用 `.venv\Scripts\python` 运行：

```bat
.venv\Scripts\python -m reverse_agent.local_reverse_console_mature_backend_probe --runtime-artifact project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json --handoff-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --triage-artifact project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
```

注意：如果 probe 因 status 非 READY 返回 exit code 1，但 artifact 正常生成，应按 artifact 内容分类为 blocked/readiness failure，不视为 Python 崩溃。

### Phase D — artifact index and report

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 至少登记：

```text
local_reverse_cpp2_2f64e68d_pywinpty_setup
local_reverse_cpp2_2f64e68d_console_mature_backend_probe
```

必须同时更新 legacy `latest_artifacts` 和 `latest_artifacts_v2`。

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m pip show pywinpty
.venv\Scripts\python -c "import winpty; print('winpty_import_ok')"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.local_reverse_console_mature_backend_probe --runtime-artifact project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json --handoff-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --triage-artifact project_state/local_reverse_cpp2_2f64e68d_static_triage.json --out project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. .venv 未被 git 跟踪。
2. git diff --name-status 不包含 .venv、site-packages、*.whl、*.dll、*.exe、sample binary 或 solve_reports。
3. pywinpty_setup artifact 存在，并记录 install/import 结果。
4. mature backend probe artifact 存在，并记录 pywinpty_available。
5. mature backend probe artifact 中 executed_target=false、runtime_validated=false、candidate=null、known_candidate=""、solved=false。
6. 如果 probe_status=READY_FOR_MATURE_BACKEND_VALIDATION，则 report 中建议下一轮进入 pywinpty-backed validator implementation/interactive validation。
7. 如果 probe 仍 blocked，则 report 中建议下一轮转 static compare-path proof 或修复 Python/backend 环境。
8. local_reverse_training_status.json 不在本轮改为 solved。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. Python 版本 < 3.9 且无法创建可用 .venv。
2. pip install pywinpty 失败且无法在本轮范围内解决。
3. import winpty 失败。
4. 需要修改全局 Python 或系统级 PATH 才能继续。
5. 需要运行目标样本或 pair validator runtime validation 才能继续。
6. 需要修改 local_reverse_console_pair_validator.py 才能继续。
7. 需要自研 terminal emulator、expect state machine 或 custom ConPTY runner。
8. git diff 显示 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills 或无关文件变更。
9. pytest、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
```

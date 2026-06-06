```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260606_cpp2_2f64e68d_pywinpty_setup_probe_test_record_closeout_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_pywinpty_setup_probe_test_record_closeout_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **engineering_branch**。

目标：对上一轮 `cpp2_2f64e68d` pywinpty setup/probe 做一次小范围 closeout，只修复审计中发现的记录缺口：

```text
1. project_state/pytest_result.txt 缺少两个 required command 记录：
   - .venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
   - .venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py

2. project_state/codex_execution_report.md 中 ConPTY 字段表述与实际 probe artifact 不一致：
   - report 写 conpty_api_available=true
   - 实际 project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json 为 conpty_api_available=false
```

本轮只补测试记录和报告表述，不继续推进验证，不实现 validator，不运行目标样本。

预期结果：

```text
project_state/pytest_result.txt 记录本轮完整命令级输出，包括 py_compile 和 mature backend probe tests。
project_state/codex_execution_report.md 与本 decision_id/round_id 匹配，并修正 ConPTY 表述为 conpty_api_available=false。
pytest/lint/status 全部重新记录。
```

本轮不得修改：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/artifact_index.json
requirements-console-backend.txt
reverse_agent/*.py
tests/*.py
local_reverse_training_status.json
```

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

上一轮 active report：

```text
report_id=report_20260606_cpp2_2f64e68d_pywinpty_setup_probe_v1
round_id=round_20260606_cpp2_2f64e68d_pywinpty_setup_probe_v1
based_on_decision_id=decision_20260606_cpp2_2f64e68d_pywinpty_setup_probe_v1
status=SUCCESS
acceptance_recommendation=ACCEPTED
```

上一轮核心目标已达成：

```text
pywinpty_setup artifact:
  setup_status=INSTALLED
  pywinpty_installed_version=3.0.3
  pywinpty_import_module=winpty
  pywinpty_import_ok=true
  executed_target=false
  runtime_validated=false
  known_candidate=""
  solved=false

mature backend probe artifact:
  winpty_available=true
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

审计限制项：

```text
1. pytest_result.txt 记录了 venv 创建、pywinpty install/import、pip show、probe、tests/test_project_state.py、lint/status/git checks。
2. pytest_result.txt 未记录：
   - py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
   - tests/test_local_reverse_console_mature_backend_probe.py
3. codex_execution_report.md 中把 conpty_api_available 写成 true，但实际 probe artifact 为 false。
```

`.gitignore` 已包含：

```text
.venv/
venv/
env/
```

本轮不需要也不允许重新安装 pywinpty；只使用现有 `.venv` 运行缺失测试。

---

## 3. Do Not Do

严禁：

```text
1. 不运行 Cpp2.exe / CPP2.exe 或任何目标样本。
2. 不运行 console pair validator 做 candidate/control validation。
3. 不实现或修改 pywinpty-backed validator。
4. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
5. 不修改 reverse_agent/local_reverse_console_mature_backend_probe.py。
6. 不修改 tests/test_local_reverse_console_mature_backend_probe.py。
7. 不重新生成 mature backend probe artifact。
8. 不重新生成 pywinpty_setup artifact。
9. 不修改 artifact_index.json。
10. 不修改 requirements-console-backend.txt。
11. 不修改 local_reverse_training_status.json / evaluation_queue.json / status_overlay.json。
12. 不把 ippio 写成 known_candidate/candidate/solved/flag。
13. 不运行 debugger、hook、emulator、CompareProbe、solver、bruteforce、guided pool。
14. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
15. 不修改 .codex-skills/*。
```

允许：

```text
1. 使用现有 .venv 运行 py_compile。
2. 使用现有 .venv 运行 tests/test_local_reverse_console_mature_backend_probe.py。
3. 运行 tests/test_project_state.py。
4. 运行 project_state lint-decision/lint-report/status。
5. 运行 git diff/status 检查。
6. 修改 project_state/codex_execution_report.md。
7. 修改 project_state/pytest_result.txt。
8. 可新建本轮 minimal round archive；但不要包含 artifact_index/current_state/negative_results/task_packet 或 git_diff.patch。
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
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
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
3. 是否确认本轮主线为 engineering_branch closeout。
4. 是否确认上一轮 pywinpty setup/probe 已完成但有测试记录/ConPTY 表述限制项。
5. 是否确认本轮没有运行目标样本。
6. 是否确认本轮没有运行 pair validator validation。
7. 是否确认本轮没有修改 validator/probe 源码或测试源码。
8. 是否确认本轮没有重新生成 setup/probe artifact。
9. 是否确认 report 中 ConPTY 表述与 artifact 一致：conpty_api_available=false。
10. 是否确认 pytest_result.txt 记录了 py_compile mature backend probe module。
11. 是否确认 pytest_result.txt 记录了 tests/test_local_reverse_console_mature_backend_probe.py。
12. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
13. 是否确认 lint-decision、lint-report、status 结果真实记录。
14. 是否确认 git status --short 和 git diff --name-status 只包含允许文件。
15. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步 closeout，不跨主线扩张。

具体执行：

```text
1. 读取 current setup/probe artifacts。
2. 确认 probe artifact 字段：
   winpty_available=true
   probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
   can_attempt_interactive_console_validation_next=true
   conpty_api_available=false
   executed_target=false
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
3. 不修改 setup/probe artifacts。
4. 运行缺失命令并记录：
   .venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
   .venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
5. 运行完整 project_state 检查。
6. 更新 codex_execution_report.md：
   - 本轮 report_id/decision_id/round_id
   - 明确上一轮 backend 已 READY
   - 明确 conpty_api_available=false，readiness 来自 winpty_available=true
   - 明确没有运行目标样本/validator validation
7. 更新 pytest_result.txt，完整记录命令、exit_code、关键输出。
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_mature_backend_probe.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_mature_backend_probe.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. setup artifact 未修改。
2. mature backend probe artifact 未修改。
3. mature backend probe artifact conpty_api_available=false。
4. mature backend probe artifact winpty_available=true。
5. mature backend probe artifact probe_status=READY_FOR_MATURE_BACKEND_VALIDATION。
6. local_reverse_training_status.json 未改为 solved。
7. git diff --name-status 只包含 project_state/codex_execution_report.md 和 project_state/pytest_result.txt，除非本轮 minimal archive 被允许生成。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 SUCCESS/ACCEPTED，如果出现任一情况：

```text
1. .venv 缺失且无法运行已安装环境的 py_compile/test。
2. py_compile 或 mature backend probe tests 失败，且无法在本轮仅通过报告修正解决。
3. 需要重新安装 pywinpty 才能继续。
4. 需要重新运行 mature backend probe 才能继续。
5. 需要运行目标样本、pair validator validation、debugger、hook、emulator、solver 或 bruteforce 才能继续。
6. git diff 显示 setup/probe artifact、artifact_index、requirements、source/test code、training status、solve_reports、.codex-skills、.venv 或二进制文件变更。
7. pytest_result.txt 仍缺少命令级输出记录。
8. report 仍声称 conpty_api_available=true。
```

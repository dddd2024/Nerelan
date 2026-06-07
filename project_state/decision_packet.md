```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_winpty_py_target_spawn_fix_v1",
  "round_id": "round_20260607_winpty_py_target_spawn_fix_v1",
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

目标：修复上一轮 synthetic winpty smoke 暴露出的 `_run_single_winpty` 对 `.py` 目标文件的 `appname/cmdline` 处理错误，并补齐本轮最终审计记录闭环。

上一轮已经证明：

```text
Phase A synthetic smoke 执行了临时 Python 脚本，不访问训练样本。
smoke_status=BLOCKED。
executed=true, timed_out=false, return_code=1。
stdout_tail 包含 SyntaxError: Non-UTF-8 code starting with '\x90' in file F:\reverse-agent\.venv\Scripts\python.exe。
failure_stage=read_drain。
Phase B cpp2_2f64e68d ippio/jppio validation 未执行。
CPP2.exe 未运行。
```

根因：当前 `_run_single_winpty` 对 `.py` 文件构造：

```python
cmd = [sys.executable, str(target_path)]
appname = sys.executable
cmdline = subprocess.list2cmdline(cmd)
pty.spawn(appname, cmdline=cmdline, cwd=str(target_path.parent))
```

在 Windows / pywinpty 下，这会导致 Python 进程把 `python.exe` 自身当作要执行的脚本，从而触发 `SyntaxError`。本轮只修复 `.py` synthetic target 的 spawn 参数构造，并用 synthetic smoke 证明修复。不得运行 `CPP2.exe`，不得重复 `ippio/jppio` runtime validation。

预期产物：

```text
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
project_state/local_reverse_winpty_py_target_spawn_fix.json
project_state/local_reverse_winpty_synthetic_smoke.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
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

当前 `project_state/current_state.json` 仍主要是旧 `samplereverse` 压缩状态。本轮不能把旧 `current_state` 当作 `cpp2_2f64e68d` 的完整事实来源；本轮事实以上一轮 report/pytest/smoke artifact、artifact_index 和现有 source/test 为准。

上一轮 decision/report 状态：

```text
decision_id=decision_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1
report_id=report_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1
report_status=BLOCKED
acceptance_recommendation=BLOCKED
```

上一轮 synthetic smoke artifact：

```text
project_state/local_reverse_winpty_synthetic_smoke.json:
  schema_version=1
  mainline=reverse_solving
  analysis_mode=winpty_synthetic_smoke
  backend=winpty
  uses_training_sample=false
  target_path_kind=temporary_python_script
  input_text=synthetic_input
  executed=true
  timed_out=false
  return_code=1
  stdout_tail contains SyntaxError for F:\reverse-agent\.venv\Scripts\python.exe
  stderr_tail="winpty read failed: "
  failure_stage=read_drain
  smoke_status=BLOCKED
  candidate=null
  known_candidate=""
  solved=false
```

上一轮 report 根因分析：

```text
When pty.spawn(appname=sys.executable, cmdline="<python.exe> <synthetic_smoke.py>") is used,
CreateProcess argument handling causes python.exe itself to be interpreted as the script.
Isolated experiment reported:
  appname=full python.exe + cmdline=full python.exe + script -> failed
  appname=python.exe + cmdline=full python.exe + script -> failed
  appname=python.exe + cmdline=script path only -> success
```

当前 winpty backend code facts：

```text
reverse_agent/local_reverse_console_pair_validator.py:
  _run_single_winpty imports winpty lazily
  creates winpty.PTY(80, 24)
  for .py target: cmd=[sys.executable, target_path], appname=sys.executable
  cmdline=subprocess.list2cmdline(cmd)
  pty.spawn(appname, cmdline=cmdline, cwd=target_path.parent)
  read/write loop and timeout cleanup already exist from prior hardening
```

当前 training status：

```text
cpp2_2f64e68d:
  training_status=blocked
  known_candidate=""
  blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
  classification=console_winpty_runtime_validation_blocked
```

negative_results 当前主要记录旧 `samplereverse` 失败方向。本轮不触碰这些旧路线，不重跑 Base64/RC4、CompareProbe、blind search、guided pool 或 solver。

已检查成熟工具能力：

```text
IDA: 已用于 cpp2 static triage / strcmp handoff；本轮不重跑。
winpty/pywinpty: import/capability 已通过；本轮修复现有 adapter 的 .py target spawn 参数。
subprocess validator: 本轮不用。
solver/bruteforce/symbolic: 本轮不用。
debugger/hook/emulator/Frida/x64dbg/OllyDbg: 本轮不用。
```

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不运行 CPP2.exe / Cpp2.exe 或任何 local_reverse_samples / E:\reverse 下的真实样本。
3. 不执行 Phase B ippio/jppio validation。
4. 不改写 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json。
5. 不把 ippio 写成 known_candidate、candidate、solved 或 flag。
6. 不修改 cpp2 static triage、strcmp handoff、pywinpty setup、mature backend probe、readiness closeout artifact。
7. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
8. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
9. 不重跑 IDA/Ghidra 静态提取。
10. 不实现自研 terminal emulator、expect DSL 或 custom ConPTY runner。
11. 不引入重型依赖、数据库、队列、Kubernetes、workflow engine。
12. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
13. 不扫描完整本地训练样本目录。
14. 不跨主线推进样本求解或训练集批量状态同步。
15. 不修改 project_state/decision_packet.md。
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_pair_validator.py 中 _run_single_winpty 对 .py target 的 appname/cmdline 构造。
2. 修改 tests/test_local_reverse_console_pair_validator.py，增加 .py target spawn 参数测试和 synthetic smoke regression 测试。
3. 使用 mock/fake winpty 对象验证 .py target 调用 pty.spawn(appname=Path(sys.executable).name, cmdline=<script path only>, cwd=<script parent>)。
4. 使用 .venv\Scripts\python 运行所有 Python commands。
5. 执行一个 synthetic winpty smoke，目标只能是临时 Python echo/readline script，不得访问训练样本。
6. 覆盖/重写 project_state/local_reverse_winpty_synthetic_smoke.json 为本轮修复后的 smoke artifact。
7. 生成 project_state/local_reverse_winpty_py_target_spawn_fix.json。
8. 更新 project_state/artifact_index.json 登记 spawn fix artifact 和 smoke artifact current provenance。
9. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
10. 若上一轮 pytest_result 中 lint-report 是旧报告 mismatch，本轮必须在写入本轮 report 后重新运行 lint-report 并记录最终成功或失败。
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
project_state/local_reverse_winpty_synthetic_smoke.json
project_state/local_reverse_winpty_backend_lifecycle_hardening.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/local_reverse_training_status.json
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/project_state.py
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
```

不要默认读取：

```text
solve_reports/ 全量
PROJECT_PROGRESS_LOG.txt 全量
project_state/rounds/ 全量历史
local_reverse_samples/ 或 E:\reverse 全量目录
```

---

## 5. Required Audit

Codex 报告必须回答：

```text
1. 是否确认当前 decision_packet 是本轮唯一执行权威。
2. 是否确认 task_packet.task 只是旧 samplereverse advisory。
3. 是否确认本轮主线为 tool_integration，不是 reverse_solving。
4. 是否确认上一轮 synthetic smoke BLOCKED，且 Phase B / CPP2.exe 未运行。
5. 是否确认本轮没有运行 CPP2.exe / Cpp2.exe 或任何真实训练样本。
6. 是否确认本轮没有重复 ippio/jppio validation。
7. 是否确认没有改写 cpp2 runtime validation artifact 为 solved。
8. 是否确认没有重跑 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。
9. 是否说明 .py target 原 appname/cmdline 错误和修复方式。
10. 是否确认 .py target 修复只影响 winpty backend 的 Python script target，不改变 subprocess backend。
11. 是否确认 mock/fake winpty 测试覆盖 .py target spawn 参数。
12. 是否确认 synthetic smoke 使用临时 Python 脚本，不访问训练样本、不包含 candidate/flag、不读取 E:\reverse/local_reverse_samples。
13. 是否确认 synthetic smoke artifact 写入 project_state/local_reverse_winpty_synthetic_smoke.json。
14. 是否确认 spawn fix artifact 写入 project_state/local_reverse_winpty_py_target_spawn_fix.json。
15. 是否确认 artifact_index 登记两个 artifact 的 current provenance。
16. 是否确认 cpp2_2f64e68d training status 仍为 blocked、known_candidate 仍为空、solved 未设置。
17. 是否确认所有 Python 命令都使用 .venv\Scripts\python。
18. 是否确认 lint-report 是写入本轮 report 后的最终记录，不是旧 report mismatch。
19. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
20. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
21. 是否确认 files_changed 完整列出所有实际变更文件。
22. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步修复，不跨主线扩张。

### Phase A — inspect and patch `.py` target spawn construction

在 `reverse_agent/local_reverse_console_pair_validator.py` 中只修改 `_run_single_winpty` 的 command construction 部分。

目标行为：

```python
if str(target_path).lower().endswith(".py"):
    appname = Path(sys.executable).name
    cmdline = subprocess.list2cmdline([str(target_path)])
else:
    cmd = [str(target_path)]
    appname = str(target_path)
    cmdline = subprocess.list2cmdline(cmd)
```

允许保留 `cwd=str(target_path.parent)`。不得改变 candidate/control 判定逻辑、subprocess backend、target resolution、hash check 或 validation_status 语义。

如果实际 pywinpty 要求不同参数形式，必须用 synthetic smoke 和 mock tests 证明，并在 report 中说明。

### Phase B — tests

必须新增/更新 tests，至少覆盖：

```text
1. .py target 使用 Path(sys.executable).name 作为 appname。
2. .py target cmdline 不重复包含 sys.executable。
3. .py target cmdline 包含临时 script path。
4. cwd 是 script parent。
5. .exe target 仍保持 appname=str(target_path)，cmdline=list2cmdline([target_path])。
6. subprocess backend old behavior 不变。
7. synthetic smoke regression 在当前 .venv + winpty 下能 PASS 或若 BLOCKED 则有清晰 failure_stage。
```

### Phase C — synthetic smoke

必须使用 `.venv\Scripts\python` 执行 synthetic smoke。目标只能是临时 Python 脚本，例如：

```python
print('synthetic_prompt')
line = input()
print('synthetic_seen=' + line)
```

调用 `_run_single_winpty(temp_script, "synthetic_input", timeout=10)`，写入：

```text
project_state/local_reverse_winpty_synthetic_smoke.json
```

本轮 smoke artifact 至少包含：

```text
schema_version=1
mainline=tool_integration
analysis_mode=winpty_synthetic_smoke_after_py_target_spawn_fix
backend=winpty
uses_training_sample=false
target_path_kind=temporary_python_script
input_text=synthetic_input
executed=<run.executed>
timed_out=<run.timed_out>
return_code=<run.return_code>
stdout_tail=<run.stdout_tail>
stderr_tail=<run.stderr_tail>
failure_stage=<run.failure_stage>
smoke_status=PASS|BLOCKED
candidate=null
known_candidate=""
solved=false
generated_at=<UTC>
```

PASS 条件：

```text
executed=true
timed_out=false
stdout_tail contains synthetic_seen=synthetic_input
smoke_status=PASS
```

若 smoke 仍 BLOCKED：本轮仍可 `status=BLOCKED`，但必须保留 artifact 和清晰根因；不得运行 CPP2.exe。

### Phase D — spawn fix artifact and state

生成：

```text
project_state/local_reverse_winpty_py_target_spawn_fix.json
```

字段至少包含：

```text
schema_version=1
mainline=tool_integration
analysis_mode=winpty_py_target_spawn_fix
source_smoke_artifact=project_state\local_reverse_winpty_synthetic_smoke.json
previous_failure=python_exe_interpreted_as_script
changed_file=reverse_agent/local_reverse_console_pair_validator.py
fixed_behavior=.py target uses Path(sys.executable).name appname and script-only cmdline
executed_real_sample=false
repeated_ippio_jppio_validation=false
candidate=null
known_candidate=""
solved=false
synthetic_smoke_status=<PASS|BLOCKED>
next_action=<if PASS: open separate reverse_solving decision for bounded ippio/jppio validation; if BLOCKED: continue tool_integration>
generated_at=<UTC>
```

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须同时登记：

```text
latest_artifacts["local_reverse_winpty_py_target_spawn_fix"]
latest_artifacts_v2["local_reverse_winpty_py_target_spawn_fix"]
latest_artifacts["local_reverse_winpty_synthetic_smoke"]
latest_artifacts_v2["local_reverse_winpty_synthetic_smoke"]
```

不得更新 `local_reverse_training_status.json`，除非只追加基础设施 evidence 且保持：

```text
training_status=blocked
known_candidate=""
solved 不得出现 true
```

---

## 7. Tests

所有 Python 命令必须使用 `.venv\Scripts\python`。

必须运行并记录：

```text
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import winpty; print(hasattr(winpty, 'PTY')); print([name for name in dir(winpty.PTY) if not name.startswith('_')])"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # must be final after report write or rerun after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
<synthetic winpty smoke command using .venv\Scripts\python>
git diff --check
git status --short
git diff --name-status
```

Important reporting rule：

```text
If lint-report is first run before writing the final report and fails due to stale report mismatch, it must be rerun after writing the final report. pytest_result.txt must include the final rerun result. A stale lint-report failure cannot be the only lint-report record.
```

必须做内容断言并在报告中写明：

```text
1. spawn fix artifact exists。
2. synthetic smoke artifact exists。
3. synthetic smoke uses_training_sample=false。
4. synthetic smoke candidate=null、known_candidate=""、solved=false。
5. no CPP2.exe execution。
6. no ippio/jppio validation。
7. cpp2 runtime validation artifact was not modified。
8. cpp2 training status was not marked solved。
9. artifact_index registers current provenance for spawn fix and smoke artifacts。
10. files_changed includes all modified files。
11. git diff --name-status only contains allowed files。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得继续扩大范围，如果出现任一情况：

```text
1. .venv\Scripts\python 不存在，或 .venv 内 import winpty 失败。
2. winpty API inspection 不包含 PTY.spawn/read/write/isalive/get_exitstatus/cancel_io。
3. 需要运行 CPP2.exe / Cpp2.exe 或任何真实训练样本才能继续。
4. 需要重复 ippio/jppio validation 才能继续。
5. 需要调试、hook、emulator、CompareProbe、solver、bruteforce 或重新跑 IDA/Ghidra 才能继续。
6. 需要引入重型依赖或自研 terminal emulator/expect DSL/ConPTY runner 才能继续。
7. 修改范围超过 _run_single_winpty .py target spawn construction 和相关 tests。
8. synthetic smoke 访问训练样本路径、包含 ippio/jppio 语义、或读取 E:\reverse/local_reverse_samples。
9. hardening/fix/smoke artifact 缺失或无法登记 current provenance。
10. pytest、py_compile、lint-decision、final lint-report、status 任一失败且无法在本轮范围内最小修复。
11. 任一 Python command 使用系统 python 而不是 .venv\Scripts\python。
12. git diff 显示 decision_packet.md、.venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、无关样本状态或无关工程文件变更。
13. 任何 artifact 或状态文件把 ippio 写成 known_candidate/candidate/solved。
```

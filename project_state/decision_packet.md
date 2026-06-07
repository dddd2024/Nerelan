```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_winpty_validator_lifecycle_hardening_v1",
  "round_id": "round_20260607_winpty_validator_lifecycle_hardening_v1",
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

目标：针对上一轮 `cpp2_2f64e68d` 的 bounded winpty runtime validation 被外层命令超时打断的问题，审计并硬化现有 `reverse_agent/local_reverse_console_pair_validator.py` 的 winpty backend 生命周期。

上一轮已经证明：

```text
.venv 内 import winpty 成功。
get_console_backend_capabilities()["winpty"].available=true。
get_console_backend_capabilities()["winpty"].validator_supported=true。
readiness artifact adapter_ready=true。
```

但实际运行：

```text
.venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator ... --backend winpty ...
exit_code=124
command timed out after 34441 milliseconds
validator_artifact_generated_by_cli=false
blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
```

因此本轮不是继续求解 `cpp2_2f64e68d`，而是修复/验证 winpty adapter 自身的调用方式、读写循环、超时退出、进程终止、PTY 关闭和 artifact flushing 行为。

本轮必须避免再次直接运行 `CPP2.exe` 或重复 `ippio`/`jppio` validation。只能使用 mock tests 和允许的合成小命令验证 winpty backend 生命周期；合成命令不得读取本地训练样本，不得包含候选 flag/answer 逻辑。

预期结果：

```text
1. 确认 pywinpty/winpty 的实际 API 用法，并修正当前 adapter 中不可靠的 spawn/read/write/wait/close 流程。
2. 为 winpty backend 增加有界读写、超时、清理和错误记录测试。
3. 增加一个不执行真实样本的 synthetic winpty smoke/capability artifact。
4. 不生成新的 cpp2 runtime validation，不把 ippio 标记为 solved。
5. 更新 codex_execution_report.md 和 pytest_result.txt。
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

`project_state/current_state.json` 仍主要是旧 `samplereverse` 压缩状态。本轮不能把旧 `current_state` 当作 `cpp2_2f64e68d` 的完整事实来源；本轮事实以 `artifact_index.latest_artifacts_v2`、上一轮 report/pytest/runtime artifact 和现有 source/test 为准。

当前上一轮 decision/report 状态：

```text
decision_id=decision_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1
report_id=report_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1
report_status=BLOCKED
acceptance_recommendation=BLOCKED
```

上一轮 pytest/result 关键事实：

```text
.venv\Scripts\python -c "import winpty" -> exit_code=0
capability assertion -> exit_code=0, available=True, validator_supported=True
validator CLI with --backend winpty -> exit_code=124
output=command timed out after 34441 milliseconds
note=no native runtime artifact was generated; no rerun performed to preserve max_runs boundary
```

当前 closeout artifact：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json:
  backend=winpty
  command_exit_code=124
  command_timed_out=true
  validator_artifact_generated_by_cli=false
  artifact_created_by_closeout=true
  executed_sample=unknown
  target_execution_count=unknown_after_outer_timeout
  validation_status=BLOCKED
  blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
  candidate=null
  known_candidate=""
  solved=false
  preflight.winpty_import_ok=true
  preflight.adapter_ready=true
```

当前 training status：

```text
cpp2_2f64e68d:
  training_status=blocked
  known_candidate=""
  blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
  classification=console_winpty_runtime_validation_blocked
```

注意：`local_reverse_training_status.json` 的 `cpp2_2f64e68d.evidence_sources` 仍残留旧的 `mature_backend_missing` 描述。该字段与现在 `adapter_ready=true` 不一致。本轮可以在不改变 solved 状态的前提下清理该单样本 evidence source 语义。

现有 validator 相关实现线索：

```text
reverse_agent/local_reverse_console_pair_validator.py:
  get_console_backend_capabilities() dynamically detects winpty
  validate_console_pair(..., backend="winpty") selects _run_single_winpty
  CLI supports --backend choices=["subprocess", "winpty"]
  _run_single_winpty imports winpty lazily
  _run_single_winpty creates winpty.PTY(80, 24)
  _run_single_winpty currently couples PTY with subprocess.Popen stdin/stdout/stderr
  _run_single_winpty writes input, waits for proc, then reads terminal output
```

这说明问题不在 import/capability 注册层，而在实际 winpty process lifecycle 层。Codex 必须检查 pywinpty/winpty 的真实 API，而不是继续基于假设调用。

当前 negative_results 仍主要是旧 `samplereverse` 失败方向。本轮不触碰旧 samplereverse 路线，不重跑 Base64/RC4、CompareProbe、blind search、guided pool 或 solver。

已有成熟工具接口：

```text
IDA: 已用于 cpp2 static triage / strcmp handoff；本轮不重跑。
winpty/pywinpty: import/capability 可用；本轮审计 adapter 调用方式。
subprocess validator: 已产生 AMBIGUOUS_OUTPUT；本轮不重复。
solver/bruteforce/symbolic: 本轮不用。
debugger/hook/emulator/Frida/x64dbg/OllyDbg: 本轮不用。
```

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不直接重跑 cpp2_2f64e68d 的 ippio/jppio runtime validation。
3. 不运行 CPP2.exe / Cpp2.exe 或任何 local_reverse_samples / E:\reverse 下的真实样本。
4. 不生成新的 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json，除非只是保留现有 blocked artifact 不改写。
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
```

允许：

```text
1. 修改 reverse_agent/local_reverse_console_pair_validator.py 中现有 winpty backend 调用、超时、清理和错误记录逻辑。
2. 修改 tests/test_local_reverse_console_pair_validator.py，或新增最小 winpty backend lifecycle test 文件。
3. 使用 mock/fake winpty 对象测试 spawn/read/write/timeout/close 顺序。
4. 使用 .venv\Scripts\python 运行 import/capability checks。
5. 如果当前 Windows .venv 有 winpty，可执行一个 synthetic winpty smoke 命令；命令只能是 Python 自身或小型无样本 echo/readline 程序，不得运行训练样本。
6. 生成 project_state/local_reverse_winpty_backend_lifecycle_hardening.json。
7. 更新 project_state/artifact_index.json 登记 hardening artifact current provenance。
8. 可清理 local_reverse_training_status.json 中 cpp2_2f64e68d 的过期 evidence_sources 语义，但不得改变 blocked/solved 状态。
9. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
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
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/local_reverse_training_status.json
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/project_state.py
tests/test_local_reverse_console_mature_backend_probe.py
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
4. 是否确认上一轮 winpty import/capability/readiness 均通过。
5. 是否确认上一轮实际 validator CLI 超时 exit_code=124，且无原生 artifact。
6. 是否确认本轮没有运行 CPP2.exe / Cpp2.exe 或任何真实训练样本。
7. 是否确认本轮没有重复 ippio/jppio validation。
8. 是否确认没有改写 cpp2 runtime validation artifact 为 solved。
9. 是否确认没有重跑 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。
10. 是否说明 pywinpty/winpty 的实际 API 检查结果。
11. 是否说明原实现卡住的最可能生命周期原因。
12. 是否说明 winpty backend 的修复点：spawn/read/write/wait/timeout/kill/close/artifact flushing。
13. 是否说明 mock tests 覆盖哪些异常路径。
14. 如果执行 synthetic smoke，是否确认它不使用训练样本、不包含 candidate/flag、不超过小型 echo/readline 行为。
15. 是否确认 hardening artifact 写入 project_state/local_reverse_winpty_backend_lifecycle_hardening.json。
16. 是否确认 artifact_index 登记 hardening artifact current provenance。
17. 是否确认 cpp2_2f64e68d training status 仍为 blocked、known_candidate 仍为空、solved 未设置。
18. 如果清理 stale evidence source，是否只触碰 cpp2_2f64e68d，不改其他样本。
19. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
20. 是否确认 git diff --name-status 只包含允许文件。
21. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步修复，不跨主线扩张。

### Phase A — inspect actual winpty API and current failure surface

必须使用 `.venv\Scripts\python` 执行无样本 API/capability 检查，例如：

```bat
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print(winpty); print(hasattr(winpty, 'PTY')); print(dir(winpty.PTY))"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
```

如果 winpty API 不支持现有设计，报告必须明确写出不支持点，并把本轮 status 写为 BLOCKED 或 REWORK_REQUIRED；不得转向自研 terminal emulator。

### Phase B — harden `_run_single_winpty`

在现有 `reverse_agent/local_reverse_console_pair_validator.py` 中做最小修复。应关注：

```text
1. 使用 pywinpty/winpty 的真实 spawn API，而不是假设 PTY 对象可直接作为 subprocess stdio。
2. 建立有界 read loop，不要 proc.wait 后才首次读取导致缓冲/交互卡死。
3. 写入 input_text + newline 后，必要时发送第二个 newline 但必须可测试、可解释。
4. timeout 到达时可靠终止 child process / PTY，并记录 timed_out=true。
5. finally 中必须 close PTY，且 close 异常不得吞掉主要错误上下文。
6. run record 必须记录 backend="winpty"、executed、timed_out、return_code、stdout_tail、stderr_tail、failure stage。
7. validate_console_pair / CLI 必须仍能在 BLOCKED/AMBIGUOUS 情况下返回 artifact，而不是让外层命令无产物超时。
```

不得改变 subprocess backend 的既有行为，除非为了共享纯辅助函数且测试覆盖兼容性。

### Phase C — tests

必须新增或更新 mock tests，覆盖至少：

```text
1. winpty available 时选择 winpty runner。
2. winpty import failure 返回 unsupported runtime/blocking record，不崩溃。
3. PTY creation failure 返回清晰 stderr/failure stage。
4. spawn/write/read 正常路径能收集 stdout_tail 并退出。
5. read loop timeout 后 timed_out=true，且 close/kill 被调用。
6. read/close 异常不会导致 CLI 无 artifact。
7. CLI --backend winpty 在 mocked BLOCKED 情况下仍写出 output artifact。
```

可选 synthetic smoke：

```text
仅在 Windows + .venv winpty 可用时运行。
命令只能使用 .venv Python 执行一个 echo/readline 小脚本。
不得运行 CPP2.exe 或任何训练样本。
如果 smoke 不稳定，必须记录为 BLOCKED/limitation，不得重跑真实样本绕过。
```

### Phase D — artifacts and state

生成：

```text
project_state/local_reverse_winpty_backend_lifecycle_hardening.json
```

字段至少包含：

```text
schema_version=1
mainline=tool_integration
analysis_mode=winpty_backend_lifecycle_hardening
source_blocked_artifact=project_state\local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
source_readiness_artifact=project_state\local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
winpty_import_ok=<bool>
capability_available=<bool>
capability_validator_supported=<bool>
inspected_api_summary=<short text>
fixed_lifecycle_points=[...]
mock_tests_added=[...]
synthetic_smoke_ran=<bool>
synthetic_smoke_status=<PASS|SKIPPED|BLOCKED>
executed_real_sample=false
repeated_ippio_jppio_validation=false
candidate=null
known_candidate=""
solved=false
next_action="after audit acceptance, open separate reverse_solving decision for bounded ippio/jppio validation"
generated_at=<UTC>
```

更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须同时更新：

```text
latest_artifacts["local_reverse_winpty_backend_lifecycle_hardening"]
latest_artifacts_v2["local_reverse_winpty_backend_lifecycle_hardening"]
```

允许清理但不解决：

```text
project_state/local_reverse_training_status.json 中 cpp2_2f64e68d.evidence_sources 的 stale mature_backend_missing 描述。
```

该清理必须保持：

```text
training_status=blocked
known_candidate=""
solved 不得出现 true
blocked_reason 保持 WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT 或更新为更准确的 winpty lifecycle blocker
```

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import winpty; print(winpty); print(hasattr(winpty, 'PTY')); print([name for name in dir(winpty.PTY) if not name.startswith('_')])"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增单独 test 文件，也必须运行该文件。

如执行 synthetic smoke，必须记录命令和 exit code，并明确：

```text
synthetic smoke did not run CPP2.exe
synthetic smoke did not access local_reverse_samples / E:\reverse
synthetic smoke did not validate ippio/jppio
```

必须做内容断言并在报告中写明：

```text
1. hardening artifact 存在。
2. hardening artifact executed_real_sample=false。
3. hardening artifact repeated_ippio_jppio_validation=false。
4. hardening artifact candidate=null、known_candidate=""、solved=false。
5. artifact_index 登记 current provenance。
6. cpp2 training status 未被标 solved。
7. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得继续扩大范围，如果出现任一情况：

```text
1. .venv\Scripts\python 不存在，或 .venv 内 import winpty 失败。
2. winpty API 检查表明当前 pywinpty 不支持可用 spawn/read/write 能力。
3. 需要运行 CPP2.exe / Cpp2.exe 或任何真实训练样本才能继续。
4. 需要重复 ippio/jppio validation 才能继续。
5. 需要调试、hook、emulator、CompareProbe、solver、bruteforce 或重新跑 IDA/Ghidra 才能继续。
6. 需要引入重型依赖或自研 terminal emulator/expect DSL/ConPTY runner 才能继续。
7. tests 需要改动无关模块或跨主线重构才能通过。
8. hardening artifact 缺失或无法登记 current provenance。
9. pytest、py_compile、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
10. git diff 显示 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、无关样本状态或无关工程文件变更。
11. 任何 artifact 或状态文件把 ippio 写成 known_candidate/candidate/solved。
```

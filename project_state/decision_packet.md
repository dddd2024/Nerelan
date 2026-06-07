```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **reverse_solving**。

目标：在上一轮 `winpty backend lifecycle hardening` 被审计为 `ACCEPTED_WITH_LIMITATIONS` 后，重新执行 `cpp2_2f64e68d` 的 **bounded winpty runtime validation**，验证静态候选 `ippio` 是否能在修复后的 winpty backend 下被明确接受，且 same-length negative control `jppio` 是否被明确拒绝。

本轮必须分两阶段执行：

```text
Phase A: synthetic winpty smoke，不运行真实训练样本，只验证 winpty backend 能 spawn/read/write/timeout/close 并写出 artifact。
Phase B: 只有 Phase A PASS 时，才允许执行一次 cpp2_2f64e68d 的 ippio/jppio winpty validation。
```

本轮要验证的问题很窄：

```text
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
static_candidate_text=ippio
negative_control_input=jppio
backend=winpty
max_runs=2
```

预期产物：

```text
project_state/local_reverse_winpty_synthetic_smoke.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json   # only if outcome requires status sync
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 `ippio` 在 winpty backend 下被明确接受、`jppio` 被明确拒绝，则可以把 `cpp2_2f64e68d` 标记为 solved，并同步相关 project_state 状态文件。若 synthetic smoke 失败、validator CLI 超时、输出仍 ambiguous，或 backend/target 执行失败，必须保守记录 BLOCKED / ACCEPTED_WITH_LIMITATIONS，不得把 `ippio` 写成 solved。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

`project_state/current_state.json` 仍主要是旧 `samplereverse` 压缩状态。本轮不能把旧 `current_state` 当作 `cpp2_2f64e68d` 的完整事实来源；本轮事实以 `artifact_index.latest_artifacts_v2`、current cpp2 artifacts、上一轮 hardening artifact、上一轮审计限制项和现有 validator 源码为准。

当前 artifact_index 已登记以下 current evidence：

```text
local_reverse_cpp2_2f64e68d_static_triage: current
local_reverse_cpp2_2f64e68d_strcmp_handoff: current
local_reverse_cpp2_2f64e68d_runtime_pair_validation: current, old subprocess AMBIGUOUS_OUTPUT
local_reverse_cpp2_2f64e68d_pywinpty_setup: current
local_reverse_cpp2_2f64e68d_console_mature_backend_probe: current
local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness: current
local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation: current, blocked by WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
local_reverse_winpty_backend_lifecycle_hardening: current
```

静态工具证据：

```text
project_state/local_reverse_cpp2_2f64e68d_static_triage.json:
  ida_attempted=true
  ida_success=true
  source_tool=IDA
  status=STATIC_TRIAGE_COMPLETE
  executed_sample=false
  runtime_validated=false
```

静态候选证据：

```text
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json:
  analysis_mode=direct_strcmp_static_handoff
  source_tool=IDA
  compare_call_ea=0x40111C
  compare_callee=_strcmp
  compare_nearby='push offset Str2; "ippio" ... push ecx; Str1'
  static_candidate_text=ippio
  static_candidate_hex=697070696f
  status=READY_FOR_RUNTIME_VALIDATION
  runtime_validated=false
  solved=false
```

旧 subprocess runtime validation 证据：

```text
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json:
  backend was subprocess/basic path
  candidate_input=ippio
  negative_control_input=jppio
  max_runs=2
  executed_sample=true
  validation_status=AMBIGUOUS_OUTPUT
  outputs_differ=false
  runtime_validated=false
  solved=false
  blocked_reason=AMBIGUOUS_OUTPUT
```

旧 winpty runtime validation closeout 证据：

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

上一轮 hardening 证据：

```text
project_state/local_reverse_winpty_backend_lifecycle_hardening.json:
  mainline=tool_integration
  analysis_mode=winpty_backend_lifecycle_hardening
  winpty_import_ok=true
  capability_available=true
  capability_validator_supported=true
  inspected_api_summary says PTY.spawn/read/write/isalive/get_exitstatus/cancel_io are available
  fixed_lifecycle_points include PTY.spawn, bounded nonblocking read loop, CRLF input, timeout cancel_io, bounded cleanup, structured run record
  synthetic_smoke_ran=false
  synthetic_smoke_status=SKIPPED
  executed_real_sample=false
  repeated_ippio_jppio_validation=false
  candidate=null
  known_candidate=""
  solved=false
```

上一轮审计限制项：

```text
1. hardening accepted only with limitations.
2. Codex modified decision_packet.md in the previous round; do not repeat unless explicitly instructed.
3. Some lint/status commands used system python instead of .venv; this round must use .venv\Scripts\python for all Python commands.
4. Actual pywinpty API inspection listed no close() method, while code has a bounded optional close call; synthetic smoke must check that this does not block artifact creation.
5. No synthetic smoke or real bounded validation has yet proven the hardened path against a real process.
```

Current training status：

```text
cpp2_2f64e68d:
  training_status=blocked
  known_candidate=""
  blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT
  classification=console_winpty_runtime_validation_blocked
  evidence_sources include local_reverse_winpty_backend_lifecycle_hardening
  next_action=After accepting winpty lifecycle hardening, run a separate bounded ippio/jppio validation decision.
```

已检查成熟工具能力：

```text
IDA: 已用于 current static triage / strcmp handoff；本轮不重跑 IDA。
winpty/pywinpty: import/capability/hardening artifact 均 current；本轮使用现有 adapter，不改 adapter。
subprocess validator: 已产生 AMBIGUOUS_OUTPUT；本轮不重复 subprocess 路径。
solver/bruteforce/symbolic: 本轮不用。
debugger/hook/emulator/Frida/x64dbg/OllyDbg: 本轮不用。
```

negative_results 当前主要记录旧 `samplereverse` 失败方向。本轮不得触碰这些旧方向，不得回到 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 或 solver/bruteforce。

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不修改 project_state/decision_packet.md。
3. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
4. 不修改 tests/test_local_reverse_console_pair_validator.py。
5. 不重跑 IDA/Ghidra 静态提取。
6. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
7. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
8. 不重复 subprocess runtime_pair_validation；本轮真实验证必须使用 --backend winpty。
9. 不扩大 candidate pool，不测试除 ippio 和 same-length negative control jppio 外的其他候选。
10. Phase B 不超过 2 次目标样本执行：candidate 一次、negative control 一次。
11. 不在 Phase A synthetic smoke 中访问 E:\reverse、local_reverse_samples 或任何训练样本路径。
12. 不把 synthetic smoke 结果当作样本 solved。
13. 不把 ambiguous 输出当作 solved。
14. 不把 ippio 写入 known_candidate/candidate/solved，除非 artifact 显示 VALIDATED_SUCCESS、runtime_validated=true、candidate_accepted=true、control_rejected=true。
15. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
16. 不扫描完整本地训练样本目录。
17. 不做工程重构、接口重写或泛化设计。
```

允许：

```text
1. 使用 .venv\Scripts\python 运行所有 Python commands。
2. 执行一个 synthetic winpty smoke，目标只能是临时 Python echo/readline script 或等价小命令，禁止读取训练样本。
3. 生成 project_state/local_reverse_winpty_synthetic_smoke.json。
4. 只有 synthetic smoke PASS 时，运行一次现有 validator CLI 对 cpp2_2f64e68d 做 --backend winpty candidate/control validation。
5. 覆盖/重写 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json 为本轮原生 validator CLI 输出；如果 CLI 未生成 artifact，必须写 BLOCKED closeout artifact 且不得重跑。
6. 更新 project_state/artifact_index.json 中 smoke 和 runtime validation 的 current provenance。
7. 根据 validation outcome 有界更新 project_state/local_reverse_training_status.json 中 cpp2_2f64e68d 这一条。
8. 如 validation_status=VALIDATED_FAILURE 或 AMBIGUOUS_OUTPUT，可更新 project_state/negative_results.json，记录不要无新增证据重复同一 ippio/jppio winpty validation。
9. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
10. 可新建本轮 minimal round archive，但不得包含 bulky artifact、solve_reports、样本二进制或 git_diff.patch。
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
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_runtime_pair_validation.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
project_state/local_reverse_winpty_backend_lifecycle_hardening.json
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
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认上一轮 hardening artifact 是 current，且 executed_real_sample=false、repeated_ippio_jppio_validation=false。
5. 是否确认上一轮 hardening 审计限制项已纳入本轮门槛。
6. 是否确认本轮没有修改 decision_packet/source/test。
7. 是否确认所有 Python 命令都使用 .venv\Scripts\python。
8. 是否确认 Phase A synthetic smoke 不访问训练样本、不包含 ippio/jppio 语义、不读取 E:\reverse/local_reverse_samples。
9. 是否确认 synthetic smoke artifact 写入 project_state/local_reverse_winpty_synthetic_smoke.json。
10. 如果 synthetic smoke 未 PASS，是否确认没有运行 CPP2.exe。
11. 如果 synthetic smoke PASS，是否确认 Phase B 只运行一次 validator CLI，backend=winpty，candidate=ippio，negative_control=jppio，max_runs=2。
12. 是否确认没有运行除该 bounded validator 外的其他 target execution。
13. 是否确认没有调试、hook、emulate、CompareProbe、solver、bruteforce、symbolic search。
14. 是否确认没有重跑 IDA/Ghidra 静态提取。
15. 是否确认 runtime artifact 是本轮 validator CLI 原生输出；若不是，必须说明 closeout artifact 原因。
16. 是否确认 runtime artifact backend=winpty，target sha256 匹配 cpp2_2f64e68d。
17. 如果 validation_status=VALIDATED_SUCCESS，是否确认 runtime_validated=true、candidate=ippio、known_candidate=ippio、solved=true、candidate_accepted=true、control_rejected=true。
18. 如果 validation_status 不是 VALIDATED_SUCCESS，是否确认没有把 ippio 写成 solved/known_candidate。
19. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 登记 smoke 和 runtime validation artifact current provenance。
20. 是否说明 local_reverse_training_status 是否同步；若未同步，必须给出理由。
21. 是否说明 negative_results 是否更新；若未更新，必须给出理由。
22. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
23. 是否确认 git diff --name-status 只包含允许文件。
24. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步验证，不跨主线扩张。

### Phase A — preflight and synthetic winpty smoke

必须使用 `.venv\Scripts\python`：

```bat
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import winpty; print(hasattr(winpty, 'PTY')); print([name for name in dir(winpty.PTY) if not name.startswith('_')])"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
```

然后执行一个 synthetic smoke。推荐方式：用临时目录创建一个最小 Python 脚本，脚本只读取 stdin 并输出固定 marker，例如：

```python
print('synthetic_prompt')
line = input()
print('synthetic_seen=' + line)
```

用 `.venv\Scripts\python` 调用一个内联脚本，导入 `reverse_agent.local_reverse_console_pair_validator._run_single_winpty` 对该临时 Python 脚本执行一次，不触碰训练样本路径。结果写入：

```text
project_state/local_reverse_winpty_synthetic_smoke.json
```

smoke artifact 至少包含：

```text
schema_version=1
mainline=reverse_solving
analysis_mode=winpty_synthetic_smoke
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

Phase A PASS 条件：

```text
executed=true
timed_out=false
stdout_tail contains synthetic_seen=synthetic_input
smoke_status=PASS
```

如果 Phase A 未 PASS：

```text
停止。
不运行 CPP2.exe。
写 report status=BLOCKED 或 FAILED。
artifact_index 只登记 smoke artifact。
training status 保持 blocked，known_candidate=""。
```

### Phase B — bounded cpp2 winpty pair validation

只有 Phase A PASS 才允许运行：

```bat
.venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator ^
  --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json ^
  --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json ^
  --candidate-field static_candidate_text ^
  --backend winpty ^
  --timeout 10 ^
  --out project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
```

注意：该命令在 `VALIDATED_SUCCESS` / `VALIDATED_FAILURE` 时 exit code 为 0；在 `AMBIGUOUS_OUTPUT` / `BLOCKED` 时可能 exit code 为 1。若 exit code 为 1，不得自动重跑；必须读取生成的 artifact 并按 artifact 内容写报告。

若外层命令超时或没有生成原生 artifact：

```text
不重跑。
写 BLOCKED closeout artifact。
blocked_reason=WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT or more precise reason
candidate=null
known_candidate=""
solved=false
```

runtime artifact 必须满足：

```text
sample_id=cpp2_2f64e68d
analysis_mode=console_runtime_pair_validation
mainline=reverse_solving
backend=winpty
candidate_input=ippio
negative_control_input=jppio
negative_control_strategy=single_char_mutation
max_runs=2
target_sha256=2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1
```

结果处理规则：

```text
A. VALIDATED_SUCCESS:
   runtime_validated=true
   candidate=ippio
   known_candidate=ippio
   solved=true
   candidate_accepted=true
   control_rejected=true
   可以同步 local_reverse_training_status.json 中 cpp2_2f64e68d 为 solved。

B. VALIDATED_FAILURE:
   runtime_validated=true
   candidate=null
   known_candidate=""
   solved=false
   必须记录 ippio 被当前 winpty pair validation 否定；可以更新 negative_results.json。
   不得生成新候选。

C. AMBIGUOUS_OUTPUT:
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
   blocked_reason=AMBIGUOUS_OUTPUT
   可以同步 training status 为 blocked/ambiguous backend validation；可以更新 negative_results.json，避免无新证据重复 ippio/jppio winpty pair validation。

D. BLOCKED:
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
   blocked_reason 必须具体，例如 TARGET_MISSING、TARGET_MISMATCH、UNSUPPORTED_BACKEND、TIMEOUT、WINPTY_VALIDATOR_COMMAND_TIMEOUT_NO_ARTIFACT。
   不得标 solved。
```

### Phase C — project_state updates

必须更新：

```text
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

artifact_index 必须同时更新：

```text
latest_artifacts["local_reverse_winpty_synthetic_smoke"]
latest_artifacts_v2["local_reverse_winpty_synthetic_smoke"]
```

若 Phase B 执行，则还必须同时更新：

```text
latest_artifacts["local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation"]
```

`latest_artifacts_v2` 字段至少包含：

```text
kind=<artifact kind>
path=<project_state path>
freshness=current
source_run=round_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d or synthetic
```

允许根据 validation outcome 有界更新：

```text
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
project_state/negative_results.json
```

但只能触碰 `cpp2_2f64e68d`，不得重建全量 inventory，不得改其他样本状态。

### Phase D — report

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1",
  "based_on_decision_id": "decision_20260607_cpp2_2f64e68d_winpty_revalidation_after_hardening_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚：

```text
synthetic smoke 是否 PASS；
Phase B 是否执行；
runtime validation outcome；
是否写出了原生 validator artifact；
如果 solved，证据是什么；
如果未 solved，阻塞原因是什么。
```

---

## 7. Tests

必须运行并记录，所有 Python 命令都必须使用 `.venv\Scripts\python`：

```text
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import winpty; print(hasattr(winpty, 'PTY')); print([name for name in dir(winpty.PTY) if not name.startswith('_')])"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
<synthetic winpty smoke command using .venv\Scripts\python>
<if synthetic PASS> .venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --candidate-field static_candidate_text --backend winpty --timeout 10 --out project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. synthetic smoke artifact 存在。
2. synthetic smoke artifact uses_training_sample=false。
3. synthetic smoke artifact candidate=null、known_candidate=""、solved=false。
4. 如果 smoke_status != PASS，则没有运行 CPP2.exe。
5. 如果 Phase B 执行，runtime artifact 存在。
6. 如果 Phase B 执行，runtime artifact backend=winpty。
7. 如果 Phase B 执行，runtime artifact max_runs=2。
8. 如果 Phase B 执行，runtime artifact candidate_input=ippio。
9. 如果 Phase B 执行，runtime artifact negative_control_input=jppio。
10. 如果 Phase B 执行，runtime artifact target_sha256 matches cpp2_2f64e68d。
11. 如果 validation_status=VALIDATED_SUCCESS，则 runtime_validated=true、known_candidate=ippio、solved=true。
12. 如果 validation_status!=VALIDATED_SUCCESS，则 known_candidate=""、solved=false。
13. artifact_index 登记 current provenance。
14. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 solved，如果出现任一情况：

```text
1. .venv\Scripts\python 不存在，或 .venv 内 import winpty 失败。
2. winpty API inspection 不包含 PTY.spawn/read/write/isalive/get_exitstatus/cancel_io。
3. current static triage / strcmp handoff / hardening artifact 缺失或 freshness 不可确认。
4. static_candidate_text 不是 ippio。
5. validator 不支持 --backend winpty。
6. synthetic smoke 访问训练样本路径、包含 ippio/jppio 语义、或未能写出 artifact。
7. synthetic smoke 未 PASS，但仍运行了 CPP2.exe。
8. target 缺失或 sha256 与 cpp2_2f64e68d 不匹配。
9. winpty run 超时、无法创建 PTY、无法执行 target，或只执行了 candidate/control 之一。
10. 需要修改 decision_packet/source/test 代码才能继续。
11. 需要运行除 ippio/jppio 之外的额外候选才能继续。
12. 需要调试、hook、emulator、bruteforce、symbolic search 或重新跑 IDA/Ghidra 才能继续。
13. artifact 输出 runtime_validated=true 但缺少 candidate_accepted/control_rejected 证据。
14. validation_status 不是 VALIDATED_SUCCESS 却把 ippio 写成 known_candidate、candidate 或 solved。
15. artifact_index 无法登记 current provenance。
16. pytest、py_compile、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
17. 任一 Python command 使用系统 python 而不是 .venv\Scripts\python。
18. git diff 显示 decision_packet.md、source/test code、.venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、无关样本状态或无关文件变更。
```

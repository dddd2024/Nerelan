```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1",
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

目标：在上一轮已完成 `.venv` / winpty adapter readiness closeout 的基础上，对 `cpp2_2f64e68d` 的静态候选 `ippio` 执行一次 **有界 winpty interactive console runtime validation**。

本轮要验证的问题很窄：

```text
sample_id=cpp2_2f64e68d
relative_path=逆向课程2025春03/CPP2.exe
static_candidate_text=ippio
negative_control_input=jppio
backend=winpty
max_runs=2
```

允许运行目标样本，但只允许通过现有 `reverse_agent.local_reverse_console_pair_validator` 的 `--backend winpty` 路径执行候选/负例各一次。不得调试、hook、emulate、bruteforce 或扩展搜索空间。

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果 `ippio` 在 winpty backend 下被明确接受、`jppio` 被明确拒绝，则可以把 `cpp2_2f64e68d` 标记为 solved，并同步相关 project_state 状态文件。若输出仍 ambiguous 或 backend/target 执行失败，必须保守记录 BLOCKED / ACCEPTED_WITH_LIMITATIONS，不得把 `ippio` 写成 solved。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

当前 `project_state/current_state.json` 仍主要是旧 `samplereverse` 压缩状态。本轮不能把旧 `current_state` 当作 `cpp2_2f64e68d` 的完整状态来源；`cpp2_2f64e68d` 的证据以 `artifact_index.latest_artifacts_v2` 和下列 current artifacts 为准。

当前 artifact_index 已登记以下 current evidence：

```text
local_reverse_cpp2_2f64e68d_static_triage: current
local_reverse_cpp2_2f64e68d_strcmp_handoff: current
local_reverse_cpp2_2f64e68d_runtime_pair_validation: current
local_reverse_cpp2_2f64e68d_pywinpty_setup: current
local_reverse_cpp2_2f64e68d_console_mature_backend_probe: current
local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness: current
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

旧 runtime validation 证据：

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

上一轮 readiness closeout 证据：

```text
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json:
  python_executable_kind=.venv
  setup_status=INSTALLED
  probe_status=READY_FOR_MATURE_BACKEND_VALIDATION
  recommended_backend=winpty
  adapter_backend_name=winpty
  adapter_registered=true
  adapter_available=true
  adapter_validator_supported=true
  adapter_ready=true
  executed_target=false
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false
```

现有工具接口证据：

```text
reverse_agent/local_reverse_console_pair_validator.py:
  get_console_backend_capabilities() dynamically detects winpty
  validate_console_pair(..., backend="winpty") selects _run_single_winpty
  CLI supports --backend choices=["subprocess", "winpty"]
  max pair validation runs are candidate + generated negative control
```

negative_results 当前主要记录旧 `samplereverse` 失败方向。本轮不得触碰这些旧方向，不得回到 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 或 solver/bruteforce。

已检查成熟工具能力：

```text
IDA: 已用于 current static triage / strcmp handoff；本轮不重跑 IDA。
winpty: adapter_available=true 且 validator_supported=true；本轮使用现有 adapter，不重写 terminal emulator。
subprocess validator: 已产生 AMBIGUOUS_OUTPUT；本轮不重复 subprocess 路径。
solver/bruteforce/symbolic: 本轮不用。
debugger/hook/emulator/Frida/x64dbg/OllyDbg: 本轮不用。
training inventory: 不扫描全量样本目录；只允许针对 cpp2_2f64e68d 做验证后状态同步。
```

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不重跑旧 samplereverse 方向，不扫描完整 solve_reports，不读取完整 PROJECT_PROGRESS_LOG.txt。
3. 不重复 subprocess runtime_pair_validation；本轮必须使用 --backend winpty。
4. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
5. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
6. 不重跑 IDA/Ghidra 静态提取，除非当前 artifact 缺失或 hash/provenance 明确冲突；默认不得重建 static triage。
7. 不修改 reverse_agent/local_reverse_console_pair_validator.py。
8. 不修改 tests/test_local_reverse_console_pair_validator.py。
9. 不实现自研 terminal emulator、expect DSL、custom ConPTY runner 或替代 winpty adapter。
10. 不扩大 candidate pool，不测试除 ippio 和一个 same-length negative control 外的其他候选。
11. 不超过 2 次目标样本执行：candidate 一次、negative control 一次。
12. 不把 ambiguous 输出当作 solved。
13. 不把 ippio 写入 known_candidate/candidate/solved，除非 artifact 显示 VALIDATED_SUCCESS、runtime_validated=true、candidate_accepted=true、control_rejected=true。
14. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
15. 不扫描完整本地训练样本目录。
16. 不做工程重构、接口重写或泛化设计。
```

允许：

```text
1. 使用 .venv\Scripts\python 调用现有 validator CLI。
2. 读取 current cpp2_2f64e68d static/runtime/readiness artifacts。
3. 生成 project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json。
4. 更新 project_state/artifact_index.json 中该 runtime validation artifact 的 current provenance。
5. 仅在验证结果明确时，同步 project_state/local_reverse_training_status.json 中 cpp2_2f64e68d 的状态。
6. 若验证明确失败或仍 ambiguous，可更新 project_state/negative_results.json，记录不要无新增证据重复同一 ippio/jppio winpty pair validation。
7. 更新 project_state/codex_execution_report.md 和 project_state/pytest_result.txt。
8. 可新建本轮 minimal round archive，但不得包含 bulky artifact、solve_reports、样本二进制或 git_diff.patch。
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
project_state/local_reverse_cpp2_2f64e68d_pywinpty_setup.json
project_state/local_reverse_cpp2_2f64e68d_console_mature_backend_probe.json
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
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
3. 是否确认本轮主线为 reverse_solving。
4. 是否确认 IDA static triage / strcmp handoff 是 current artifact。
5. 是否确认静态候选来自 direct strcmp literal operand，static_candidate_text=ippio。
6. 是否确认旧 subprocess validation 为 AMBIGUOUS_OUTPUT，不能复用为 solved。
7. 是否确认 winpty readiness artifact 为 adapter_ready=true。
8. 是否确认本轮使用 .venv\Scripts\python 和 --backend winpty。
9. 是否确认 validator 只运行 candidate=ippio 和 negative_control=jppio，各一次，max_runs=2。
10. 是否确认没有运行除 CPP2.exe 这 2 次验证外的其他 target execution。
11. 是否确认没有调试、hook、emulate、CompareProbe、solver、bruteforce、symbolic search。
12. 是否确认没有修改 validator/source/test 代码。
13. 是否确认没有重跑 IDA/Ghidra 静态提取。
14. 是否确认 runtime artifact 的 backend=winpty，target sha256 匹配 cpp2_2f64e68d。
15. 是否确认如果 validation_status=VALIDATED_SUCCESS，则 runtime_validated=true、candidate=ippio、known_candidate=ippio、solved=true、candidate_accepted=true、control_rejected=true。
16. 是否确认如果 validation_status 不是 VALIDATED_SUCCESS，则没有把 ippio 写成 solved/known_candidate。
17. 是否确认 artifact_index latest_artifacts/latest_artifacts_v2 登记 pywinpty runtime validation artifact current provenance。
18. 是否说明 local_reverse_training_status 是否同步；若未同步，必须给出理由。
19. 是否说明 negative_results 是否更新；若未更新，必须给出理由。
20. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
21. 是否确认 git diff --name-status 只包含允许文件。
22. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步验证，不跨主线扩张。

### Phase A — preflight readiness checks

必须使用 `.venv\Scripts\python`：

```bat
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
```

检查 readiness artifact：

```text
project_state/local_reverse_cpp2_2f64e68d_winpty_validator_adapter_readiness.json
```

必须确认：

```text
adapter_ready=true
adapter_available=true
adapter_validator_supported=true
executed_target=false
runtime_validated=false
solved=false
```

若 preflight 失败：停止，写 BLOCKED；不得运行 target；不得修改 validator。

### Phase B — bounded winpty pair validation

运行现有 CLI，一次 candidate + 一次 negative control：

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
   blocked_reason 必须具体，例如 TARGET_MISSING、TARGET_MISMATCH、UNSUPPORTED_BACKEND、TIMEOUT。
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
latest_artifacts["local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation"]
```

`latest_artifacts_v2` 字段至少包含：

```text
kind=local_reverse_console_winpty_runtime_validation
path=project_state\local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
freshness=current
source_run=round_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
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
  "report_id": "report_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1",
  "based_on_decision_id": "decision_20260607_cpp2_2f64e68d_bounded_winpty_runtime_validation_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚 validation outcome，而不是只写“运行完成”。

---

## 7. Tests

必须运行并记录：

```text
.venv\Scripts\python -c "import sys; print(sys.executable); import winpty; print('winpty_import_ok')"
.venv\Scripts\python -c "import reverse_agent.local_reverse_console_pair_validator as v; caps=v.get_console_backend_capabilities(); print(caps['winpty']); assert caps['winpty']['available'] is True; assert caps['winpty']['validator_supported'] is True"
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
.venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json --candidate-field static_candidate_text --backend winpty --timeout 10 --out project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. pywinpty runtime validation artifact 存在。
2. backend=winpty。
3. max_runs=2。
4. candidate_input=ippio。
5. negative_control_input=jppio。
6. target_sha256 与 cpp2_2f64e68d 匹配。
7. 如果 validation_status=VALIDATED_SUCCESS，则 runtime_validated=true、known_candidate=ippio、solved=true。
8. 如果 validation_status!=VALIDATED_SUCCESS，则 known_candidate=""、solved=false。
9. artifact_index 登记 current provenance。
10. git diff --name-status 只包含允许文件。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 solved，如果出现任一情况：

```text
1. .venv\Scripts\python 不存在，或 .venv 内 import winpty 失败。
2. readiness artifact 不是 adapter_ready=true。
3. current static triage / strcmp handoff artifact 缺失或 freshness 不可确认。
4. static_candidate_text 不是 ippio。
5. validator 不支持 --backend winpty。
6. target 缺失或 sha256 与 cpp2_2f64e68d 不匹配。
7. winpty run 超时、无法创建 PTY、无法执行 target，或只执行了 candidate/control 之一。
8. 需要修改 validator/source/test 代码才能继续。
9. 需要运行除 ippio/jppio 之外的额外候选才能继续。
10. 需要调试、hook、emulator、bruteforce、symbolic search 或重新跑 IDA/Ghidra 才能继续。
11. artifact 输出 runtime_validated=true 但缺少 candidate_accepted/control_rejected 证据。
12. validation_status 不是 VALIDATED_SUCCESS 却把 ippio 写成 known_candidate、candidate 或 solved。
13. artifact_index 无法登记 current provenance。
14. pytest、py_compile、lint-decision、lint-report、status 任一失败且无法在本轮范围内最小修复。
15. git diff 显示 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports、.codex-skills、无关样本状态或 source/test code 变更。
```

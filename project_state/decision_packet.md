```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1",
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

目标：基于上一轮已经确认的 `cpp2_2f64e68d` post-strcmp oracle，先从静态目标字符串 `ippio` 逆推出真正的原始输入 `10013`，再做一次 **有界 oracle-backed winpty runtime validation**。

关键修正：

```text
ippio 不是用户应输入的 raw candidate。
ippio 是程序对用户输入做数字变换后的 strcmp 目标字符串。
```

必须先生成 raw input candidate artifact：

```text
static_target_after_transform=ippio
transform=(7 + 3*(digit_value)) % 10 + 105
raw_candidate_input=10013
negative_control_input=20013
```

然后最多运行目标样本两次：

```text
candidate run: 10013
negative control run: 20013
backend: winpty
max_runs: 2
```

判定依据不能再使用 raw stdout 直接比较，必须使用上一轮 oracle：

```text
success signal: stripped stdout contains "Ok, you know it"
failure signal: stripped stdout contains "Sorry! Hang on"
```

只有当 `10013` 产生 success signal 且 `20013` 产生 failure signal，才允许把 `cpp2_2f64e68d` 标记为 solved，并写入 `known_candidate=10013`。否则必须保持 blocked/unsolved。

预期产物：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json
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

上一轮 oracle extraction 已确认：

```text
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json:
  sample_id=cpp2_2f64e68d
  analysis_mode=post_strcmp_oracle_extraction
  oracle_status=ORACLE_CONFIRMED
  compare_call_ea=0x40111C
  compare_callee=_strcmp
  candidate_from_static=ippio
  executed_sample=false
  runtime_validated=false
  known_candidate=""
  solved=false
  success_path.action=puts("Ok, you know it. Just hang on.")
  failure_path.action=puts("Sorry! Hang on!")
  can_classify_runtime_output=true
  classification_method=ANSI-strip then substring match success/failure strings
```

上一轮 winpty pair validation 不是成功：

```text
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json:
  candidate_input=ippio
  negative_control_input=jppio
  validation_status=AMBIGUOUS_OUTPUT
  runtime_validated=false
  candidate_accepted=false
  control_rejected=false
  known_candidate=""
  solved=false
```

当前 training status：

```text
project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=blocked
  cpp2_2f64e68d.known_candidate=""
  cpp2_2f64e68d.classification=post_strcmp_oracle_confirmed_awaiting_runtime_revalidation
```

输入逆变换依据来自 oracle artifact 的 `pre_strcmp_transform`：

```text
Str1[j] = (7 + 3*(Str1[j] - 48)) % 10 + 105
input characters must be digits 0-9
```

对 `ippio` 求逆：

```text
target char i = 105 => y=0 => digit=1
target char p = 112 => y=7 => digit=0
target char p = 112 => y=7 => digit=0
target char i = 105 => y=0 => digit=1
target char o = 111 => y=6 => digit=3
raw_candidate_input=10013
```

负控必须同长度、全数字、且只扰动一位：

```text
negative_control_input=20013
```

已有相关能力必须优先复用：

```text
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/local_reverse_ida_summary.py
reverse_agent/local_reverse_forced_ida_extract.py
reverse_agent/ida_scripts/extract_named_data.py
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
```

`negative_results.json` 主要记录旧 `samplereverse` 禁止方向。本轮不得触碰旧 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 等方向。

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不修改 project_state/decision_packet.md。
3. 不把 ippio 当作 raw input candidate。
4. 不重复上一轮 ippio/jppio validation。
5. 不运行 solver、bruteforce、guided pool、symbolic search、constraint recovery。
6. 不运行 IDA/Ghidra 静态提取；上一轮 oracle 已足够。
7. 不运行 debugger、OllyDbg、x64dbg、Frida hook、emulator、CompareProbe。
8. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt、本地训练样本目录。
9. 不改 .codex-skills。
10. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
11. 不修改 reverse_agent/local_reverse_console_pair_validator.py，除非先停止并报告需要单独 tool_integration decision。
12. 不用 raw stdout tails 直接判定 success；必须 ANSI-strip/清洗后匹配 oracle 字符串。
13. 不超过 2 次真实目标样本执行。
14. 不测试除 10013 和 20013 外的其他候选。
15. 不把样本标 solved，除非 runtime artifact 明确 VALIDATED_SUCCESS、candidate_accepted=true、control_rejected=true、known_candidate=10013、solved=true。
```

允许：

```text
1. 读取 current static/oracle/runtime artifacts。
2. 生成 raw input candidate artifact，记录 10013 的逆变换推导。
3. 使用现有 console_pair_validator 的 winpty backend 对 10013/20013 做最多一次 pair run。
4. 如果现有 validator 只能输出 AMBIGUOUS_OUTPUT，可基于该 raw runtime artifact 再生成一个 oracle-backed classification artifact；不得重跑目标。
5. 若需要代码支持，最多新增一个小型通用 helper：reverse_agent/local_reverse_oracle_runtime_classifier.py，用于 ANSI stripping 和 oracle string matching；该 helper 必须消费 oracle artifact 与 runtime artifact，不得执行目标样本，不得硬编码 cpp2。
6. 如果新增 helper，必须新增或更新直接测试。
7. 更新 artifact_index、local_reverse_training_status、codex_execution_report、pytest_result。
8. 如 runtime 输出仍缺少 success/failure 字符串，保持 blocked/unsolved。
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
project_state/local_reverse_cpp2_2f64e68d_static_triage.json
project_state/local_reverse_cpp2_2f64e68d_strcmp_handoff.json
project_state/local_reverse_cpp2_2f64e68d_pywinpty_runtime_validation.json
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
project_state/local_reverse_training_status.json
reverse_agent/local_reverse_console_pair_validator.py
tests/test_local_reverse_console_pair_validator.py
tests/test_project_state.py
```

必要时读取：

```text
reverse_agent/project_state.py
reverse_agent/local_reverse_compare_site.py
reverse_agent/local_reverse_direct_strcmp_handoff.py
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
4. 是否确认上一轮 oracle_status=ORACLE_CONFIRMED。
5. 是否确认上一轮 ippio/jppio winpty validation 是 AMBIGUOUS_OUTPUT，不是成功。
6. 是否确认 ippio 是 transformed strcmp target，不是 raw input。
7. 是否给出 raw_candidate_input=10013 的逐字符逆变换推导。
8. 是否确认 negative_control_input=20013，同长度、全数字、只扰动一位。
9. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。
10. 是否确认没有重跑 ippio/jppio。
11. 是否确认最多运行 CPP2.exe 两次，且只运行 10013/20013。
12. 是否说明使用了现有 console_pair_validator winpty backend 还是只做 artifact classification。
13. 是否说明 ANSI stripping / oracle string matching 的实现方式。
14. 是否报告 candidate_run/control_run 的 executed、timed_out、return_code、stdout_tail/stderr_tail 摘要。
15. 是否确认 candidate cleaned stdout 包含 success signal，control cleaned stdout 包含 failure signal；若不是，必须保持 blocked。
16. 如果 VALIDATED_SUCCESS，是否确认 runtime_validated=true、candidate=10013、known_candidate=10013、solved=true、candidate_accepted=true、control_rejected=true。
17. 如果不是 VALIDATED_SUCCESS，是否确认 known_candidate=""、solved=false。
18. 是否更新 artifact_index latest_artifacts 和 latest_artifacts_v2 的 current provenance。
19. 是否有界更新 local_reverse_training_status，仅触碰 cpp2_2f64e68d。
20. 是否说明 negative_results 是否更新；若未更新，必须给出理由。
21. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
22. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
23. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
24. 是否确认 files_changed 完整列出所有实际变更文件。
25. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步推进，不跨主线扩张。

### Phase A — preflight and raw candidate derivation

必须使用 `.venv\Scripts\python`。先读取并断言：

```text
project_state/local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json:
  oracle_status=ORACLE_CONFIRMED
  candidate_from_static=ippio
  can_classify_runtime_output=true
  success_path observable stdout contains Ok, you know it
  failure_path observable stdout contains Sorry! Hang on!
  known_candidate=""
  solved=false

project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=blocked
  cpp2_2f64e68d.known_candidate=""
```

生成：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
```

该 artifact 至少包含：

```text
schema_version=1
sample_id=cpp2_2f64e68d
mainline=reverse_solving
analysis_mode=raw_input_candidate_from_post_strcmp_oracle
source_artifact=project_state\local_reverse_cpp2_2f64e68d_post_strcmp_oracle_extraction.json
source_artifact_freshness=current
executed_sample=false
runtime_validated=false
transformed_target=ippio
transform=(7 + 3*digit_value) % 10 + 105
inverse_derivation=[per-character proof]
raw_candidate_input=10013
negative_control_input=20013
candidate=null
known_candidate=""
solved=false
generated_at=<timestamp>
```

### Phase B — bounded winpty run for raw candidate/control

只允许运行一次 pair command，最多两次目标样本执行：

```bat
.venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator ^
  --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json ^
  --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json ^
  --candidate-field raw_candidate_input ^
  --backend winpty ^
  --timeout 10 ^
  --out project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json
```

注意：该现有 validator 可能仍返回 AMBIGUOUS_OUTPUT。不得因为 CLI exit code=1 就重跑。必须读取产物进入 Phase C。

### Phase C — oracle-backed classification

用上一轮 oracle artifact 和 Phase B runtime artifact 生成：

```text
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
```

分类规则：

```text
cleaned_candidate_stdout = strip_ansi(candidate_run.stdout_tail)
cleaned_control_stdout = strip_ansi(negative_control_run.stdout_tail)

candidate_accepted = cleaned_candidate_stdout contains "Ok, you know it"
control_rejected = cleaned_control_stdout contains "Sorry! Hang on"
```

结果处理：

```text
A. VALIDATED_SUCCESS:
   runtime_validated=true
   candidate=10013
   known_candidate=10013
   solved=true
   candidate_accepted=true
   control_rejected=true
   local_reverse_training_status.cpp2_2f64e68d.training_status=solved
   classification=oracle_backed_winpty_runtime_validation

B. VALIDATED_FAILURE:
   runtime_validated=true
   candidate=null
   known_candidate=""
   solved=false
   reason must specify which oracle signal contradicted expectation
   may update negative_results with raw candidate failure evidence

C. AMBIGUOUS_OUTPUT:
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
   blocked_reason=ORACLE_SIGNAL_MISSING_OR_AMBIGUOUS

D. BLOCKED:
   runtime_validated=false
   candidate=null
   known_candidate=""
   solved=false
   blocked_reason specific: TARGET_MISSING, TARGET_MISMATCH, TIMEOUT, UNSUPPORTED_BACKEND, RAW_RUNTIME_ARTIFACT_MISSING, ORACLE_ARTIFACT_MISSING
```

如果现有代码无法 conveniently classify without sample execution，可新增：

```text
reverse_agent/local_reverse_oracle_runtime_classifier.py
tests/test_local_reverse_oracle_runtime_classifier.py
```

该 helper 限制：

```text
1. 只能消费 oracle artifact 和 runtime artifact。
2. 不执行目标样本。
3. 不硬编码 cpp2、10013、20013；信号来自 oracle artifact。
4. 只做 ANSI stripping、stdout substring classification、artifact 写出。
```

### Phase D — project_state updates

必须更新：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
project_state/artifact_index.json
project_state/local_reverse_training_status.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

根据 outcome 有界更新或保持：

```text
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
project_state/negative_results.json
```

只能触碰 `cpp2_2f64e68d`。不得重建全量 inventory，不得改其他样本状态。

artifact_index 必须登记：

```text
latest_artifacts["local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle"]
latest_artifacts["local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime"]
latest_artifacts["local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation"]
latest_artifacts_v2["local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation"]
```

`latest_artifacts_v2` 字段至少包含：

```text
kind=<specific kind>
path=<project_state path>
freshness=current
source_run=round_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1
sha256=<actual artifact sha256>
size_bytes=<actual artifact size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
```

### Phase E — report

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1",
  "based_on_decision_id": "decision_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚：

```text
1. raw candidate derivation: ippio -> 10013
2. actual target executions count
3. oracle-backed classification result
4. whether training_status was marked solved or kept blocked
```

---

## 7. Tests

所有 Python 命令必须使用 `.venv\Scripts\python`。

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
<raw input candidate derivation command; must not execute target sample>
.venv\Scripts\python -m reverse_agent.local_reverse_console_pair_validator --triage project_state/local_reverse_cpp2_2f64e68d_static_triage.json --candidate-artifact project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json --candidate-field raw_candidate_input --backend winpty --timeout 10 --out project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json
<oracle-backed classification command; must not execute target sample>
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增 `local_reverse_oracle_runtime_classifier.py`，必须额外运行：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_oracle_runtime_classifier.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_oracle_runtime_classifier.py
```

必须做内容断言并在报告中写明：

```text
1. raw input candidate artifact exists。
2. raw_candidate_input=10013。
3. negative_control_input=20013。
4. raw runtime artifact exists。
5. raw runtime artifact backend=winpty。
6. raw runtime artifact max_runs=2。
7. oracle-backed runtime artifact exists。
8. oracle-backed artifact candidate_input=10013。
9. oracle-backed artifact negative_control_input=20013。
10. oracle-backed artifact candidate/control cleaned stdout signals recorded。
11. 如果 VALIDATED_SUCCESS，则 known_candidate=10013 且 solved=true。
12. 如果不是 VALIDATED_SUCCESS，则 known_candidate="" 且 solved=false。
13. artifact_index registers current provenance for all new artifacts。
14. git diff --name-status only contains allowed files。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得写 solved，如果出现任一情况：

```text
1. oracle artifact 缺失、stale、或 oracle_status 不是 ORACLE_CONFIRMED。
2. raw inverse derivation 不能证明 ippio -> 10013。
3. 负控不是同长度全数字单点扰动。
4. 需要运行除 10013/20013 外的其他候选。
5. 需要重跑 ippio/jppio。
6. 需要 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce 才能继续。
7. winpty run 超时、target missing、target sha256 mismatch、或只运行了 candidate/control 之一。
8. cleaned stdout 中 success/failure signal 缺失或同时出现导致 ambiguity。
9. 必须修改现有 console validator 才能继续；这种情况应停止并要求单独 tool_integration decision。
10. artifact 想把 ippio 写成 known_candidate 或 solved。
11. pytest_result.txt 无法对应本 decision_id/report_id/round_id。
12. lint-report 在最终报告写入后仍失败。
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1",
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

目标：修复上一轮 `cpp2_2f64e68d` oracle-backed runtime validation 的审计问题。不得重跑样本，除非明确发现 artifact 缺失。核心任务是修正 provenance、报告/测试记录，并明确 `system("pause")` 导致的 timeout 与 oracle signal 已捕获之间的语义关系。

上一轮已有有效 stdout 证据：

```text
raw_candidate_input=10013
negative_control_input=20013
candidate stdout contains "Ok, you know it. Just hang on."
control stdout contains "Sorry! Hang on!"
```

但上一轮不能直接 ACCEPT，原因是：

```text
1. raw winpty pair runtime artifact 中 candidate/control 均 timed_out=true。
2. 上一轮 decision_packet 的 stop condition 写明 winpty run 超时必须停止，不得写 solved。
3. artifact_index 三个新 artifact 的 source_run 与当前 round_id 不一致。
4. report_id 不符合上一轮 decision_packet 模板。
5. pytest_result 缺少 py_compile reverse_agent/local_reverse_console_pair_validator.py。
6. pytest_result 缺少 tests/test_project_state.py。
```

本轮允许二选一：

```text
A. 保守回滚：把 cpp2_2f64e68d 恢复为 blocked/unsolved。
B. 补充证明并保留 solved：明确 timeout 是 system("pause") 后的非阻塞型 timeout，且 success/failure oracle signal 已在 timeout 前完整捕获。
```

推荐 **方案 B**，因为现有 runtime stdout 已经同时证明 candidate success 和 control failure；但必须把规则写进 artifact/report，不得默默绕过 stop condition。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

上一轮 decision/report：

```text
previous_decision_id=decision_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1
previous_round_id=round_20260607_cpp2_2f64e68d_oracle_backed_raw_input_validation_v1
previous_report_id=report_20260607_cpp2_2f64e68d_raw_input_oracle_backed_revalidation_v1
```

上一轮 raw candidate derivation artifact：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json:
  transformed_target=ippio
  raw_candidate_input=10013
  negative_control_input=20013
  known_candidate=""
  solved=false
```

上一轮 raw runtime artifact：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json:
  candidate_input=10013
  negative_control_input=20013
  backend=winpty
  max_runs=2
  candidate_run.executed=true
  candidate_run.timed_out=true
  candidate_run.stdout_tail contains "Ok, you know it. Just hang on."
  negative_control_run.executed=true
  negative_control_run.timed_out=true
  negative_control_run.stdout_tail contains "Sorry! Hang on!"
  blocked_reason=TIMEOUT
```

上一轮 oracle-backed artifact 当前状态：

```text
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json:
  validation_status=VALIDATED_SUCCESS
  runtime_validated=true
  candidate_input=10013
  negative_control_input=20013
  candidate_accepted=true
  control_rejected=true
  known_candidate=10013
  solved=true
```

当前 training status：

```text
project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013
  cpp2_2f64e68d.classification=oracle_backed_runtime_validated
```

当前 artifact_index 问题：

```text
latest_artifacts_v2 for three new artifacts uses:
  source_run=round_20260607_cpp2_2f64e68d_raw_input_oracle_backed_revalidation_v1

But current rework round must use:
  source_run=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1

or explicitly preserve previous source_run and add rework provenance fields explaining why.
```

已有相关能力：

```text
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_oracle_runtime_classifier.py
tests/test_local_reverse_oracle_runtime_classifier.py
tests/test_local_reverse_console_pair_validator.py
tests/test_project_state.py
```

`negative_results.json` 主要记录旧 `samplereverse` 禁止方向。本轮不得触碰旧 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 等方向。

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不修改 .codex-skills。
3. 不运行 CPP2.exe / Cpp2.exe，除非发现上一轮 runtime artifact 缺失或不可读取；正常情况下不得重跑样本。
4. 不运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。
5. 不测试新候选。
6. 不重跑 ippio/jppio。
7. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt、本地训练样本目录。
8. 不扩大到其他样本。
9. 不把 ippio 写成 known_candidate 或 solved candidate。
10. 不在没有解释 timeout 语义的情况下保留 solved=true。
11. 不忽略 artifact_index source_run/report_id/pytest_result mismatch。
12. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
```

允许：

```text
1. 读取并复核上一轮三个 cpp2 artifacts。
2. 不重跑样本，直接基于已有 raw runtime stdout 进行 reclassification/provenance repair。
3. 修改 oracle-backed runtime validation artifact，增加 timeout_after_oracle_signal_captured 等解释字段。
4. 或选择保守回滚，改回 blocked/unsolved。
5. 修正 artifact_index provenance。
6. 修正 codex_execution_report.md 和 pytest_result.txt。
7. 补跑缺失测试。
8. 只触碰 cpp2_2f64e68d 相关 project_state 和必要测试/工具文件。
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
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
project_state/local_reverse_training_status.json
reverse_agent/local_reverse_console_pair_validator.py
reverse_agent/local_reverse_oracle_runtime_classifier.py
tests/test_local_reverse_oracle_runtime_classifier.py
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
4. 是否承认上一轮违反了 timeout stop condition。
5. 是否确认本轮没有重跑 CPP2.exe / Cpp2.exe。
6. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。
7. 是否确认上一轮 raw candidate 是 10013，negative control 是 20013。
8. 是否确认 raw runtime artifact 中 candidate/control 均 timed_out=true。
9. 是否确认 candidate stdout 已捕获 success signal。
10. 是否确认 control stdout 已捕获 failure signal。
11. 是否选择方案 A 回滚还是方案 B 补充证明并保留 solved。
12. 如果选择方案 B，是否在 artifact/report 中明确 timeout_source=system_pause 且 timeout_after_oracle_signal_captured=true。
13. 如果选择方案 B，是否明确该 validation 依赖 stdout oracle signal，不依赖正常 exit code。
14. 如果选择方案 A，是否把 training_status 改回 blocked、known_candidate=""。
15. 是否修正或解释 artifact_index 三个新 artifact 的 source_run。
16. 是否修正 report_id 与本 rework decision/round 对齐。
17. 是否补跑 py_compile reverse_agent/local_reverse_console_pair_validator.py。
18. 是否补跑 tests/test_project_state.py。
19. 是否重新运行 py_compile/test for oracle classifier。
20. 是否重新运行 lint-decision/lint-report/status/git checks。
21. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
22. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
23. 是否确认 files_changed 完整列出所有实际变更文件。
24. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步推进，不跨主线扩张。

### Phase A — preflight

必须使用 `.venv\Scripts\python`。先读取并断言：

```text
raw candidate artifact exists
raw_candidate_input=10013
negative_control_input=20013
raw runtime artifact exists
candidate_run.executed=true
negative_control_run.executed=true
candidate_run.timed_out=true
negative_control_run.timed_out=true
candidate stdout contains "Ok, you know it. Just hang on."
control stdout contains "Sorry! Hang on!"
oracle-backed artifact exists
```

如果上述任一项缺失，停止并写 `status=BLOCKED`。不要重跑样本，除非报告明确说明 artifact 缺失且用户下一轮批准 runtime rerun。

### Phase B — choose resolution

必须二选一并记录。

#### 方案 A：保守回滚

适用条件：无法证明 timeout 是 `system("pause")` 后发生，或不愿改变上一轮 stop condition 语义。

操作：

```text
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json:
  validation_status=BLOCKED
  runtime_validated=false
  candidate=null
  known_candidate=""
  solved=false
  blocked_reason=TIMEOUT_AFTER_SIGNAL_CAPTURE_REQUIRES_POLICY_DECISION

project_state/local_reverse_training_status.json:
  training_status=blocked
  known_candidate=""
  blocked_reason=TIMEOUT_AFTER_SIGNAL_CAPTURE_REQUIRES_POLICY_DECISION
  classification=oracle_backed_runtime_signal_captured_but_timeout_policy_blocked
```

#### 方案 B：补充证明并保留 solved

适用条件：基于 raw stdout 能确认 success/failure oracle signal 已在 timeout 前完整捕获，且 timeout 来源是 `system("pause")` 的等待按键，不影响 oracle verdict。

操作：在 oracle-backed runtime validation artifact 中增加或修正：

```text
validation_status=VALIDATED_SUCCESS
runtime_validated=true
candidate=10013
known_candidate=10013
solved=true
candidate_accepted=true
control_rejected=true
timeout_after_oracle_signal_captured=true
timeout_source=system_pause
timeout_treated_as_non_blocking_for_oracle_classifier=true
exit_code_required_for_oracle_verdict=false
oracle_verdict_source=ansi_stripped_stdout_substring_match
candidate_success_signal_captured_before_timeout=true
control_failure_signal_captured_before_timeout=true
rework_decision_id=decision_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1
rework_round_id=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1
```

training_status 可保留 solved，但 evidence_sources 必须追加本 rework round。

### Phase C — provenance repair

必须更新 artifact_index。对于三个上一轮新 artifact：

```text
local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle
local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime
local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation
```

可选择：

```text
1. 若 artifact 内容被本轮修改，则 source_run 必须改为 round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1，并更新 sha256/size/modified_at。
2. 若 artifact 内容未改，则保留原 source_run，但必须新增 rework_review 字段或 equivalent provenance，说明本轮审计确认/解释了它。注意 latest_artifacts_v2 schema 若不支持额外字段，优先更新被修改 artifact 的 source_run，未改 artifact 可保留原 source_run。
```

无论选择哪种，报告必须解释为什么不再存在 provenance mismatch。

### Phase D — report

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1",
  "round_id": "round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1",
  "based_on_decision_id": "decision_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚：

```text
1. 采用方案 A 还是方案 B。
2. 本轮没有重跑样本。
3. timeout 是否仍阻断 solved。
4. 最终 training_status 是 solved 还是 blocked。
5. provenance mismatch 如何处理。
6. 缺失测试如何补齐。
```

---

## 7. Tests

所有 Python 命令必须使用 `.venv\Scripts\python`。

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_console_pair_validator.py
.venv\Scripts\python -m py_compile reverse_agent/local_reverse_oracle_runtime_classifier.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_oracle_runtime_classifier.py
.venv\Scripts\python -m pytest -q tests/test_local_reverse_console_pair_validator.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

必须做内容断言并在报告中写明：

```text
1. 本轮未执行 CPP2.exe / Cpp2.exe。
2. raw_candidate_input 仍为 10013。
3. negative_control_input 仍为 20013。
4. oracle-backed runtime artifact 最终 status 与 chosen scheme 一致。
5. 如果保留 solved，则 timeout_after_oracle_signal_captured=true。
6. 如果回滚 blocked，则 known_candidate="" 且 solved=false。
7. artifact_index provenance 已修正或有明确解释。
8. pytest_result 使用本 decision_id/report_id/round_id。
9. git diff --name-status only contains allowed files。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得 ACCEPT，如果出现任一情况：

```text
1. 无法读取上一轮 raw runtime artifact。
2. raw runtime artifact 中没有 success/failure stdout signal。
3. 无法解释 timeout 与 system("pause") 的关系，又试图保留 solved。
4. artifact_index source_run/provenance 仍 mismatch 且无解释。
5. report_id / round_id / based_on_decision_id 不匹配本轮。
6. pytest_result 不匹配本轮 decision/report/round。
7. 缺少 py_compile console_pair_validator.py 或 tests/test_project_state.py。
8. lint-report 在最终报告写入后仍失败。
9. 任何产物把 ippio 写成 known_candidate。
10. 本轮重跑了样本但没有明确说明 artifact 缺失和原因。
```

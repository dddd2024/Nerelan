```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_local_reverse_post_solve_state_sync_v1",
  "round_id": "round_20260607_local_reverse_post_solve_state_sync_v1",
  "based_on_state_build_id": "state_20260602_053948_4e3984041cd7",
  "based_on_state_digest": "4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮主线是 **training_dataset**。

目标：在 `cpp2_2f64e68d` 已经通过 rework 审计并接受为 solved 后，做一次有界的 post-solve state sync，修正训练集层面的状态摘要和调度输入，避免后续轮次继续基于 stale overlay / stale queue / stale current_state 做决策。

本轮不是新样本求解，不进入 runtime validation，不运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce。

必须同步的事实：

```text
sample_id=cpp2_2f64e68d
known_candidate=10013
training_status=solved
classification=oracle_backed_runtime_validated
accepted_evidence=project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
accepted_rework_round=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1
```

预期产物：

```text
project_state/local_reverse_post_solve_state_sync.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
project_state/artifact_index.json
project_state/current_state.json
project_state/task_packet.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许在确认 `reverse_agent.project_state build` 已能安全消费 local reverse training status 的前提下使用 build 命令；否则必须用小范围同步逻辑，只更新 local reverse 相关字段，不能重建全量历史状态。

---

## 2. Current Evidence

`project_state/task_packet.json` 仍是旧 `samplereverse` advisory，不控制本轮：

```text
active_decision_packet=project_state/decision_packet.md
execution_scope=decision_packet_controls_current_round
task=Review bounded window discovery diagnostics
local_reverse_task_packet_authority_note=Advisory only; project_state/decision_packet.md remains the execution authority.
```

`project_state/current_state.json` 仍主要是旧 `samplereverse` 压缩状态，不反映 `cpp2_2f64e68d` 的 solved 事实。本轮需要修正或补充 local_reverse 当前摘要，但不得破坏旧兼容字段。

上轮已 ACCEPT 的事实：

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
  timeout_after_oracle_signal_captured=true
  timeout_source=system_pause
  timeout_treated_as_non_blocking_for_oracle_classifier=true
  oracle_verdict_source=ansi_stripped_stdout_substring_match
```

当前 `project_state/local_reverse_training_status.json` 已经显示：

```text
cpp2_2f64e68d.training_status=solved
cpp2_2f64e68d.known_candidate=10013
cpp2_2f64e68d.classification=oracle_backed_runtime_validated
```

但 `training_materials/local_reverse/status_overlay.json` 仍 stale：

```text
status_summary.solved=2
status_summary.blocked=5
cpp2_2f64e68d.training_status=blocked
cpp2_2f64e68d.known_candidate=""
cpp2_2f64e68d.blocked_reason="Windows platform but no mature backend available ..."
```

应同步为：

```text
status_summary.solved=3
status_summary.blocked=4
cpp2_2f64e68d.training_status=solved
cpp2_2f64e68d.known_candidate=10013
cpp2_2f64e68d.blocked_reason=""
```

当前 `project_state/local_reverse_evaluation_queue.json` 仍 generated_at=2026-06-06T14:26:09Z，queue policy 是 `simple_static_first_unsolved_only`。本轮应刷新 queue timestamp/provenance，并确保 queue 不包含 solved sample `cpp2_2f64e68d`。当前排第一的下一候选线索是：

```text
rank=1
sample_id=cpp2_32f1713e
relative_path=逆向课程2023春补考02/Cpp2.exe
proposed_next_mainline=tool_integration
allowed_actions=[static_triage]
forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

这只能作为下一轮线索，不能在本轮直接执行该样本。

`negative_results.json` 主要记录旧 `samplereverse` 禁止方向。本轮不得触碰旧 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 等方向。

已有能力/文件必须优先检查：

```text
reverse_agent/project_state.py
project_state/local_reverse_training_status.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
project_state/artifact_index.json
```

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不进入 reverse_solving 去分析新样本。
3. 不运行 CPP2.exe / Cpp2.exe / 任何真实训练样本。
4. 不运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
5. 不测试新候选，不打开 cpp2_32f1713e 的二进制。
6. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt、本地训练样本目录。
7. 不重建全量 inventory，除非先证明命令是有界且不会触碰样本二进制内容。
8. 不修改 .codex-skills。
9. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
10. 不把 `10013` 写入除 `cpp2_2f64e68d` 外的任何样本。
11. 不改变 `cpp2_2f64e68d` 的 solved 事实，除非发现上轮 accepted artifact 缺失或校验失败；若失败必须 BLOCKED，不得自行重验。
12. 不把 queue 中的 `cpp2_32f1713e` 当作本轮执行对象；它只能成为下一轮建议。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 local reverse training status、status overlay、evaluation queue。
3. 检查 reverse_agent/project_state.py 是否已有 build/lint/status 能力。
4. 有界更新 status_overlay、evaluation_queue、current_state、task_packet 中的 local_reverse 摘要。
5. 生成 post-solve sync artifact。
6. 更新 artifact_index current provenance。
7. 写 codex_execution_report 和 pytest_result。
8. 若工具已存在且有测试覆盖，可用已有 project_state 子命令做 lint/build/status；不得新增重型框架。
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
project_state/local_reverse_training_status.json
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
training_materials/local_reverse/status_overlay.json
project_state/local_reverse_evaluation_queue.json
reverse_agent/project_state.py
tests/test_project_state.py
```

必要时读取：

```text
project_state/local_reverse_cpp2_2f64e68d_raw_input_candidate_from_oracle.json
project_state/local_reverse_cpp2_2f64e68d_raw_input_winpty_pair_runtime.json
reverse_agent/local_reverse_oracle_runtime_classifier.py
tests/test_local_reverse_oracle_runtime_classifier.py
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
3. 是否确认本轮主线为 training_dataset。
4. 是否确认本轮没有运行任何真实样本。
5. 是否确认没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
6. 是否确认 cpp2_2f64e68d 的 accepted solved artifact 存在且 validation_status=VALIDATED_SUCCESS。
7. 是否确认 cpp2_2f64e68d known_candidate=10013 且只作用于该样本。
8. 是否修正 status_overlay 中 cpp2_2f64e68d 的 stale blocked 状态。
9. 是否修正 status_overlay.status_summary：solved=3、blocked=4、inventory_only=22、sample_count=29。
10. 是否刷新 local_reverse_evaluation_queue generated_at/source，并确认 solved sample cpp2_2f64e68d 不在 queue 中。
11. 是否保留 queue 第一项 cpp2_32f1713e 仅作为下一轮 static_triage 线索，没有执行。
12. 是否更新 current_state/task_packet 的 local_reverse 摘要，且不删除旧兼容字段。
13. 是否生成 local_reverse_post_solve_state_sync artifact，记录同步前后差异。
14. 是否更新 artifact_index latest_artifacts 和 latest_artifacts_v2 的 current provenance。
15. 是否说明 negative_results 未更新的理由。
16. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id，并记录命令、exit code、关键输出。
17. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
18. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
19. 是否确认 files_changed 完整列出所有实际变更文件。
20. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小步推进，不跨主线扩张。

### Phase A — preflight

必须使用 `.venv\Scripts\python`。

读取并断言：

```text
project_state/local_reverse_training_status.json:
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013
  cpp2_2f64e68d.classification=oracle_backed_runtime_validated

project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json:
  validation_status=VALIDATED_SUCCESS
  runtime_validated=true
  candidate=10013
  known_candidate=10013
  solved=true
  timeout_after_oracle_signal_captured=true

training_materials/local_reverse/status_overlay.json:
  cpp2_2f64e68d is currently stale/blocked OR already solved
```

如果 accepted solved artifact 缺失或不一致，停止并写 `status=BLOCKED`。不得重跑样本。

### Phase B — sync status overlay

更新 `training_materials/local_reverse/status_overlay.json`：

```text
cpp2_2f64e68d.training_status=solved
cpp2_2f64e68d.known_candidate=10013
cpp2_2f64e68d.blocked_reason=""
status_summary.solved=3
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=22
sample_count=29
generated_at=<current timestamp>
```

不得改其他样本状态，除非只是保持排序/格式导致的无语义变化；报告必须说明。

### Phase C — sync queue and summaries

更新 `project_state/local_reverse_evaluation_queue.json`：

```text
generated_at=<current timestamp>
source_status_overlay=training_materials/local_reverse/status_overlay.json
source_training_status=project_state/local_reverse_training_status.json
post_solve_sync_round_id=round_20260607_local_reverse_post_solve_state_sync_v1
exclude_solved_samples includes cpp2_2f64e68d
items must not include cpp2_2f64e68d
rank 1 may remain cpp2_32f1713e if still first unsolved/inventory-only sample
```

更新 `project_state/current_state.json` 与 `project_state/task_packet.json` 的 local_reverse 摘要字段。要求：

```text
1. 保留旧 samplereverse 字段以兼容老流程。
2. 新增或更新 local_reverse_training_summary / local_reverse_recent_solved / local_reverse_next_queue_hint 等低 token 字段。
3. 明确 task_packet.task 仍只是 advisory，execution authority remains decision_packet。
4. 不把下一样本任务写成当前轮执行权威。
```

建议摘要：

```text
local_reverse_recent_solved:
  sample_id=cpp2_2f64e68d
  known_candidate=10013
  validation_artifact=project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
  accepted_round=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1

local_reverse_training_summary:
  sample_count=29
  solved=3
  blocked=4
  inventory_only=22

local_reverse_next_queue_hint:
  sample_id=cpp2_32f1713e
  proposed_next_mainline=tool_integration
  allowed_actions=[static_triage]
  forbidden_actions=[runtime_probe, bruteforce, upload_binary]
```

### Phase D — sync artifact

生成：

```text
project_state/local_reverse_post_solve_state_sync.json
```

字段至少包含：

```text
schema_version=1
mainline=training_dataset
sync_round_id=round_20260607_local_reverse_post_solve_state_sync_v1
sync_decision_id=decision_20260607_local_reverse_post_solve_state_sync_v1
executed_sample=false
ran_static_tools=false
ran_runtime_tools=false
updated_sample_id=cpp2_2f64e68d
known_candidate=10013
accepted_validation_artifact=project_state\local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
status_overlay_before={training_status, known_candidate, blocked_reason}
status_overlay_after={training_status, known_candidate, blocked_reason}
status_summary_after={sample_count, solved, blocked, needs_triage, inventory_only}
evaluation_queue_first_item={sample_id, proposed_next_mainline, allowed_actions, forbidden_actions}
current_state_updated=true|false
task_packet_updated=true|false
generated_at=<timestamp>
```

### Phase E — artifact_index

登记：

```text
latest_artifacts["local_reverse_post_solve_state_sync"]
latest_artifacts_v2["local_reverse_post_solve_state_sync"]
```

`latest_artifacts_v2` 至少包含：

```text
kind=local_reverse_post_solve_state_sync
path=project_state\local_reverse_post_solve_state_sync.json
freshness=current
source_run=round_20260607_local_reverse_post_solve_state_sync_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
```

### Phase F — report

`codex_execution_report.md` 顶部必须包含 fenced JSON block：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_post_solve_state_sync_v1",
  "round_id": "round_20260607_local_reverse_post_solve_state_sync_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_post_solve_state_sync_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

报告必须写清楚：

```text
1. 本轮只是 training_dataset state sync，不是解新样本。
2. cpp2_2f64e68d 的 solved 证据来自已接受的 oracle-backed artifact。
3. status_overlay 与 queue 的 before/after。
4. next queue hint 只是下一轮建议，不是本轮执行。
```

---

## 7. Tests

所有 Python 命令必须使用 `.venv\Scripts\python`。

必须运行并记录：

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
<post-solve sync command or bounded script; must not execute target sample>
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

如果新增或修改任何 sync helper，必须额外运行：

```text
.venv\Scripts\python -m py_compile <helper>
.venv\Scripts\python -m pytest -q <directly related test file>
```

必须做内容断言并在报告中写明：

```text
1. 本轮未执行任何样本。
2. 本轮未运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
3. status_overlay cpp2_2f64e68d training_status=solved。
4. status_overlay cpp2_2f64e68d known_candidate=10013。
5. status_overlay summary solved=3 blocked=4 inventory_only=22 sample_count=29。
6. evaluation_queue 不包含 cpp2_2f64e68d。
7. evaluation_queue first item is recorded as next_queue_hint, not executed。
8. current_state/task_packet local_reverse summaries updated without deleting old fields。
9. local_reverse_post_solve_state_sync artifact exists and records before/after。
10. artifact_index registers current provenance。
11. pytest_result 使用本 decision_id/report_id/round_id。
12. git diff --name-status only contains allowed files。
```

---

## 8. Stop Conditions

必须停止并写 `status=BLOCKED` 或 `status=FAILED`，不得 ACCEPT，如果出现任一情况：

```text
1. accepted oracle-backed validation artifact 缺失或不再是 VALIDATED_SUCCESS。
2. local_reverse_training_status 中 cpp2_2f64e68d 不是 solved/10013。
3. 需要运行样本、IDA/Ghidra、debugger、solver、bruteforce 或 runtime probe 才能继续。
4. status_overlay 更新会影响除 cpp2_2f64e68d 外的样本状态，且没有明确说明原因。
5. evaluation_queue 仍包含 solved sample cpp2_2f64e68d。
6. current_state/task_packet 被重写到丢失旧兼容字段。
7. artifact_index 未登记 post-solve sync artifact。
8. pytest_result 不匹配本轮 decision/report/round。
9. lint-report 在最终报告写入后仍失败。
10. git diff 包含 .venv、site-packages、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

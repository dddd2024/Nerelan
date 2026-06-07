```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_local_reverse_post_solve_state_sync_rework_v1",
  "round_id": "round_20260607_local_reverse_post_solve_state_sync_rework_v1",
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

目标：修复上一轮 `local_reverse_post_solve_state_sync` 未完成项。上一轮只完成了 `training_materials/local_reverse/status_overlay.json` 的局部同步，但没有完成 decision 要求的完整 post-solve state sync。

本轮必须补齐：

```text
1. 生成 project_state/local_reverse_post_solve_state_sync.json。
2. 登记 artifact_index.latest_artifacts["local_reverse_post_solve_state_sync"]。
3. 登记 artifact_index.latest_artifacts_v2["local_reverse_post_solve_state_sync"]。
4. 更新 project_state/local_reverse_evaluation_queue.json 的 generated_at/source/post_solve_sync_round_id。
5. 更新 project_state/current_state.json 的 local_reverse_training_summary / local_reverse_recent_solved / local_reverse_next_queue_hint。
6. 更新 project_state/task_packet.json 的 local_reverse 摘要，保留 task_packet.task 只是 advisory。
7. 刷新 training_materials/local_reverse/status_overlay.json 的 generated_at。
8. 补跑 py_compile reverse_agent/project_state.py。
```

本轮不是新样本求解，不进入 reverse_solving，不运行样本、IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。

必须保持已接受事实：

```text
sample_id=cpp2_2f64e68d
training_status=solved
known_candidate=10013
accepted_validation_artifact=project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
accepted_rework_round=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1
```

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 中的 `task` 仍是旧 `samplereverse` advisory，不控制本轮。

上一轮 post-solve sync 的局部完成项：

```text
training_materials/local_reverse/status_overlay.json:
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013
  cpp2_2f64e68d.blocked_reason=""
  status_summary.solved=3
  status_summary.blocked=4
  status_summary.inventory_only=22
  sample_count=29
```

上一轮未完成项：

```text
project_state/local_reverse_post_solve_state_sync.json: missing
project_state/local_reverse_evaluation_queue.json: not modified
project_state/current_state.json: not modified; still old samplereverse compressed state
project_state/task_packet.json: not modified; still old local_reverse_next_suggested_task
training_materials/local_reverse/status_overlay.json.generated_at: still stale
pytest_result.txt: missing py_compile reverse_agent/project_state.py
artifact_index: registered local_reverse_cpp2_2f64e68d_training_status_sync instead of required local_reverse_post_solve_state_sync
```

Accepted solved evidence remains:

```text
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json:
  validation_status=VALIDATED_SUCCESS
  runtime_validated=true
  candidate=10013
  known_candidate=10013
  solved=true
  timeout_after_oracle_signal_captured=true
```

Current queue context:

```text
project_state/local_reverse_evaluation_queue.json:
  queue_policy=simple_static_first_unsolved_only
  items must not include cpp2_2f64e68d
  current first item may remain cpp2_32f1713e
  cpp2_32f1713e is only a next_queue_hint, not this round's execution object
```

`negative_results.json` mainly records old `samplereverse` forbidden directions. This rework must not touch old blind search, guided pool, Base64/RC4 breakpoint probe, CompareProbe, or other solved/blocked sample directions.

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不运行任何样本。
3. 不运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
4. 不分析 cpp2_32f1713e；它只能作为 next_queue_hint。
5. 不打开本地样本二进制，不上传或提交任何样本文件。
6. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt、本地训练样本目录。
7. 不重建全量 inventory。
8. 不修改 .codex-skills。
9. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
10. 不把 10013 写入除 cpp2_2f64e68d 外的任何样本。
11. 不改变 cpp2_2f64e68d 的 solved/10013 事实，除非 accepted validation artifact 缺失或校验失败；若失败必须 BLOCKED，不得自行重验。
12. 不删除 current_state.json 或 task_packet.json 的旧 samplereverse 兼容字段。
13. 不把 cpp2_32f1713e 写成当前执行任务；它只能作为下一轮 tool_integration/static_triage 建议。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 local_reverse_training_status、status_overlay、evaluation_queue。
3. 小范围更新 status_overlay.generated_at。
4. 小范围更新 evaluation_queue metadata/provenance，不改变队列语义，除非移除 solved sample。
5. 小范围追加 current_state/task_packet 的 local_reverse 摘要字段，保留旧字段。
6. 生成 local_reverse_post_solve_state_sync.json。
7. 更新 artifact_index current provenance。
8. 写 codex_execution_report.md 与 pytest_result.txt。
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
2. 是否承认上一轮只完成了 status_overlay 局部同步。
3. 是否确认本轮主线为 training_dataset。
4. 是否确认本轮没有运行任何样本。
5. 是否确认本轮没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
6. 是否确认 cpp2_2f64e68d 的 accepted solved artifact 存在且 validation_status=VALIDATED_SUCCESS。
7. 是否确认 cpp2_2f64e68d known_candidate=10013 且只作用于该样本。
8. 是否生成 project_state/local_reverse_post_solve_state_sync.json。
9. 是否刷新 status_overlay.generated_at。
10. 是否更新 local_reverse_evaluation_queue 的 generated_at/source_status_overlay/source_training_status/post_solve_sync_round_id。
11. 是否确认 evaluation_queue 不包含 cpp2_2f64e68d。
12. 是否把 cpp2_32f1713e 只记录为 next_queue_hint，没有执行。
13. 是否更新 current_state/task_packet local_reverse 摘要且保留旧字段。
14. 是否补跑 py_compile reverse_agent/project_state.py。
15. 是否更新 artifact_index 的 local_reverse_post_solve_state_sync provenance。
16. 是否说明 negative_results 未更新的理由。
17. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
18. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
19. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
20. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小范围修复，不新增重型工具，不跨主线扩张。

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
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013
  status_summary.solved=3
  status_summary.blocked=4
```

如果 accepted solved artifact 缺失或不一致，停止并写 `status=BLOCKED`。不得重跑样本。

### Phase B — status overlay generated_at repair

更新 `training_materials/local_reverse/status_overlay.json`：

```text
generated_at=<current timestamp>
```

不得改变除 `generated_at` 外的 overlay 语义字段，除非只是补充 provenance 字段且报告说明。尤其不得改其他样本状态。

### Phase C — evaluation queue metadata sync

更新 `project_state/local_reverse_evaluation_queue.json`：

```text
generated_at=<current timestamp>
source_status_overlay=training_materials/local_reverse/status_overlay.json
source_training_status=project_state/local_reverse_training_status.json
post_solve_sync_round_id=round_20260607_local_reverse_post_solve_state_sync_rework_v1
exclude_solved_samples includes cpp2_2f64e68d
items must not include cpp2_2f64e68d
rank 1 may remain cpp2_32f1713e if still first unsolved/inventory-only sample
```

Do not reorder the queue unless needed to remove solved samples. If ranks are unchanged, record that in report.

### Phase D — current_state/task_packet local_reverse summaries

Update `project_state/current_state.json` and `project_state/task_packet.json` by adding/updating low-token fields only. Preserve all existing fields.

Required summary fields:

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
  needs_triage=0
  inventory_only=22

local_reverse_next_queue_hint:
  sample_id=cpp2_32f1713e
  relative_path=逆向课程2023春补考02/Cpp2.exe
  proposed_next_mainline=tool_integration
  allowed_actions=[static_triage]
  forbidden_actions=[runtime_probe, bruteforce, upload_binary]

local_reverse_task_packet_authority_note:
  Advisory only; project_state/decision_packet.md remains the execution authority.
```

Do not change `task_packet.task` into cpp2_32f1713e execution. If updating `local_reverse_next_suggested_task`, it must be wording such as:

```text
Advisory next queue hint only: cpp2_32f1713e static_triage under a future tool_integration decision; do not execute from task_packet alone.
```

### Phase E — required sync artifact

Generate:

```text
project_state/local_reverse_post_solve_state_sync.json
```

Required fields:

```text
schema_version=1
mainline=training_dataset
sync_round_id=round_20260607_local_reverse_post_solve_state_sync_rework_v1
sync_decision_id=decision_20260607_local_reverse_post_solve_state_sync_rework_v1
executed_sample=false
ran_static_tools=false
ran_runtime_tools=false
updated_sample_id=cpp2_2f64e68d
known_candidate=10013
accepted_validation_artifact=project_state\local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
status_overlay_after={training_status=solved, known_candidate=10013, blocked_reason=""}
status_summary_after={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}
evaluation_queue_first_item={sample_id=cpp2_32f1713e, proposed_next_mainline=tool_integration, allowed_actions=[static_triage], forbidden_actions=[runtime_probe, bruteforce, upload_binary]}
current_state_updated=true
task_packet_updated=true
generated_at=<timestamp>
```

### Phase F — artifact_index

Register:

```text
latest_artifacts["local_reverse_post_solve_state_sync"]
latest_artifacts_v2["local_reverse_post_solve_state_sync"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_post_solve_state_sync
path=project_state\local_reverse_post_solve_state_sync.json
freshness=current
source_run=round_20260607_local_reverse_post_solve_state_sync_rework_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
```

Do not remove the earlier `local_reverse_cpp2_2f64e68d_training_status_sync` artifact; it may remain as a partial historical artifact.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_post_solve_state_sync_rework_v1",
  "round_id": "round_20260607_local_reverse_post_solve_state_sync_rework_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_post_solve_state_sync_rework_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Report must explicitly state that this is a rework of incomplete state sync and not new solving.

---

## 7. Tests

All Python commands must use `.venv\Scripts\python`.

Must run and record:

```text
.venv\Scripts\python -m py_compile reverse_agent/project_state.py
.venv\Scripts\python -m pytest -q tests/test_project_state.py
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state   # final after report write
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
git diff --check
git status --short
git diff --name-status
```

Content assertions required in report/pytest_result:

```text
1. No sample executed.
2. No IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe run.
3. status_overlay generated_at refreshed.
4. status_overlay cpp2_2f64e68d training_status=solved.
5. status_overlay cpp2_2f64e68d known_candidate=10013.
6. evaluation_queue has post_solve_sync_round_id=round_20260607_local_reverse_post_solve_state_sync_rework_v1.
7. evaluation_queue excludes cpp2_2f64e68d.
8. evaluation_queue first item recorded as next_queue_hint, not executed.
9. current_state and task_packet local_reverse summaries updated without deleting old fields.
10. local_reverse_post_solve_state_sync.json exists and records after state.
11. artifact_index registers local_reverse_post_solve_state_sync current provenance.
12. pytest_result uses this decision_id/report_id/round_id.
13. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=BLOCKED` or `status=FAILED`, not ACCEPT, if any condition occurs:

```text
1. accepted oracle-backed validation artifact is missing or not VALIDATED_SUCCESS.
2. local_reverse_training_status cpp2_2f64e68d is not solved/10013.
3. Any sample, IDA/Ghidra, debugger, hook, emulator, solver, bruteforce, or runtime probe would be needed.
4. current_state/task_packet update would delete old samplereverse compatibility fields.
5. evaluation_queue still lacks post_solve_sync_round_id.
6. evaluation_queue contains solved sample cpp2_2f64e68d.
7. local_reverse_post_solve_state_sync.json is not generated.
8. artifact_index does not register local_reverse_post_solve_state_sync.
9. pytest_result does not include py_compile reverse_agent/project_state.py.
10. pytest_result does not match this decision/report/round.
11. lint-report after final report write fails.
12. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```

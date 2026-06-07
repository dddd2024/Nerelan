```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260607_local_reverse_training_status_summary_sync_v1",
  "round_id": "round_20260607_local_reverse_training_status_summary_sync_v1",
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

目标：修复上一轮审计中留下的唯一状态一致性限制：`project_state/local_reverse_training_status.json` 顶部 `status_summary` 仍显示 `solved=2 / blocked=5`，但样本列表、`status_overlay.json`、`current_state.json` 和 post-solve sync artifact 已经确认 `cpp2_2f64e68d` 为 `solved / 10013`，训练集汇总应为：

```text
sample_count=29
solved=3
blocked=4
needs_triage=0
inventory_only=22
```

本轮只做 **training status aggregate summary sync**，不做新样本求解，不进入 `reverse_solving`，不运行样本、IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。

必须保持已接受事实：

```text
sample_id=cpp2_2f64e68d
training_status=solved
known_candidate=10013
classification=oracle_backed_runtime_validated
accepted_validation_artifact=project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json
accepted_rework_round=round_20260607_cpp2_2f64e68d_oracle_backed_validation_rework_v1
post_solve_sync_artifact=project_state/local_reverse_post_solve_state_sync.json
```

---

## 2. Current Evidence

当前 `decision_packet.md` 是本轮唯一执行权威。`project_state/task_packet.json` 中的 `task` 仍是旧 `samplereverse` advisory，不控制本轮。

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`，限制点为：

```text
project_state/local_reverse_training_status.json:
  top-level status_summary still says solved=2, blocked=5, inventory_only=22.

But sample entry cpp2_2f64e68d says:
  training_status=solved
  known_candidate=10013
  classification=oracle_backed_runtime_validated
```

已同步的新事实：

```text
training_materials/local_reverse/status_overlay.json:
  generated_at=2026-06-07T15:00:00Z
  status_summary.solved=3
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=22
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013

project_state/local_reverse_post_solve_state_sync.json:
  mainline=training_dataset
  executed_sample=false
  ran_static_tools=false
  ran_runtime_tools=false
  updated_sample_id=cpp2_2f64e68d
  known_candidate=10013
  status_summary_after={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}

project_state/artifact_index.json:
  latest_artifacts_v2.local_reverse_post_solve_state_sync.freshness=current
  source_run=round_20260607_local_reverse_post_solve_state_sync_rework_v1
```

`negative_results.json` 主要记录旧 `samplereverse` 禁止方向。本轮是训练集状态汇总同步，不应新增 negative result，也不得触碰旧 blind search、guided pool、Base64/RC4 breakpoint probe、CompareProbe 或任意样本求解方向。

现有相关能力：

```text
project_state lint-decision / lint-report / status already exists.
tests/test_project_state.py already covers project_state lint behavior.
artifact_index latest_artifacts and latest_artifacts_v2 both exist and must be kept compatible.
```

---

## 3. Do Not Do

严禁：

```text
1. 不把 task_packet.task 当作当前轮任务。
2. 不运行任何样本。
3. 不运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
4. 不分析 cpp2_32f1713e；它只能继续作为 next_queue_hint。
5. 不打开本地样本二进制，不上传或提交任何样本文件。
6. 不扫描完整 solve_reports、PROJECT_PROGRESS_LOG.txt、本地训练样本目录。
7. 不重建全量 inventory。
8. 不修改 .codex-skills。
9. 不提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports。
10. 不改变任何样本的 training_status / known_candidate / blocked_reason / classification。
11. 不把 10013 写入除 cpp2_2f64e68d 外的任何样本。
12. 不删除 current_state.json、task_packet.json、artifact_index.json 的旧兼容字段。
13. 不把 cpp2_32f1713e 写成当前执行任务；它只能作为下一轮 tool_integration/static_triage 建议。
14. 不修改 reverse_agent 源码，除非 lint 工具本身无法读取现有状态；若需要源码修改，停止并写 BLOCKED。
```

允许：

```text
1. 读取默认 project_state 文件。
2. 读取 .codex-skills/registry.json 以确认 skill profile 合法。
3. 读取 local_reverse_training_status、status_overlay、evaluation_queue、post_solve_state_sync、accepted validation artifact。
4. 小范围更新 project_state/local_reverse_training_status.json 的 generated_at、status_summary、兼容计数字段和 provenance 字段。
5. 生成 project_state/local_reverse_training_status_summary_sync.json。
6. 更新 artifact_index.latest_artifacts 和 latest_artifacts_v2，登记 local_reverse_training_status_summary_sync。
7. 必要时在 current_state/task_packet 添加一个低 token 的 summary_sync artifact 指针；不得改变 task_packet.task。
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
project_state/local_reverse_post_solve_state_sync.json
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
2. 是否确认本轮主线为 training_dataset。
3. 是否确认本轮只是 aggregate summary sync，不是新样本求解。
4. 是否确认本轮没有运行任何样本。
5. 是否确认本轮没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。
6. 是否确认 accepted validation artifact 存在且 validation_status=VALIDATED_SUCCESS。
7. 是否确认 cpp2_2f64e68d known_candidate=10013 且只作用于该样本。
8. 是否确认 status_overlay summary 为 solved=3 blocked=4 inventory_only=22。
9. 是否确认 local_reverse_training_status 样本列表中 cpp2_2f64e68d 已是 solved/10013。
10. 是否更新 local_reverse_training_status 顶部 status_summary 为 solved=3 blocked=4 needs_triage=0 inventory_only=22。
11. 是否同步 legacy 兼容字段 solved_count=3 blocked_count=4 inventory_only_count=22。
12. 是否未改变任何 samples[] 条目的 training_status/known_candidate/blocked_reason/classification。
13. 是否生成 project_state/local_reverse_training_status_summary_sync.json。
14. 是否更新 artifact_index 的 latest_artifacts 和 latest_artifacts_v2。
15. 是否说明 negative_results 未更新的理由。
16. 是否确认 task_packet.task 未变成 cpp2_32f1713e 执行任务。
17. 是否确认 cpp2_32f1713e 仍只是 next_queue_hint，没有执行。
18. 是否补跑 py_compile reverse_agent/project_state.py。
19. 是否确认 pytest_result.txt 使用本 decision_id/report_id/round_id。
20. 是否确认 final lint-report 是写入本轮 report 后的最终成功记录。
21. 是否确认 git diff --check、git status --short、git diff --name-status 均有真实输出记录。
22. 是否确认没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills。
```

---

## 6. Implementation Scope

小范围修复，不新增工具，不跨主线扩张。

### Phase A — preflight

必须使用 `.venv\Scripts\python`。

读取并断言：

```text
project_state/local_reverse_cpp2_2f64e68d_oracle_backed_runtime_validation.json:
  validation_status=VALIDATED_SUCCESS
  runtime_validated=true
  candidate=10013
  known_candidate=10013
  solved=true
  timeout_after_oracle_signal_captured=true

project_state/local_reverse_post_solve_state_sync.json:
  mainline=training_dataset
  executed_sample=false
  ran_static_tools=false
  ran_runtime_tools=false
  updated_sample_id=cpp2_2f64e68d
  known_candidate=10013
  status_summary_after.solved=3
  status_summary_after.blocked=4
  status_summary_after.needs_triage=0
  status_summary_after.inventory_only=22

training_materials/local_reverse/status_overlay.json:
  status_summary.solved=3
  status_summary.blocked=4
  status_summary.needs_triage=0
  status_summary.inventory_only=22
  cpp2_2f64e68d.training_status=solved
  cpp2_2f64e68d.known_candidate=10013
```

如果 accepted validation artifact 或 post-solve sync artifact 缺失、不一致，停止并写 `status=BLOCKED`。不得重跑样本。

### Phase B — compute aggregate from samples[]

从 `project_state/local_reverse_training_status.json.samples[]` 重新计算：

```text
sample_count = len(samples)
solved = count(training_status == "solved")
blocked = count(training_status == "blocked")
needs_triage = count(training_status == "needs_triage")
inventory_only = count(training_status == "inventory_only")
```

断言结果必须为：

```text
sample_count=29
solved=3
blocked=4
needs_triage=0
inventory_only=22
```

若计算结果不是上述值，停止并写 `status=BLOCKED`，不要手工覆盖。

### Phase C — update local_reverse_training_status summary only

更新 `project_state/local_reverse_training_status.json` 顶部字段：

```text
generated_at=<current timestamp>
status_summary.solved=3
status_summary.blocked=4
status_summary.needs_triage=0
status_summary.inventory_only=22
status_summary.solved_count=3
status_summary.blocked_count=4
status_summary.inventory_only_count=22
```

可追加低 token provenance：

```text
summary_sync_round_id=round_20260607_local_reverse_training_status_summary_sync_v1
summary_sync_decision_id=decision_20260607_local_reverse_training_status_summary_sync_v1
summary_source_status_overlay=training_materials/local_reverse/status_overlay.json
summary_source_post_solve_sync=project_state/local_reverse_post_solve_state_sync.json
```

不得修改 `samples[]` 中任何样本的状态、候选、分类、路径、sha256、evidence_sources 或 next_action。

### Phase D — generate summary sync artifact

生成：

```text
project_state/local_reverse_training_status_summary_sync.json
```

Required fields:

```text
schema_version=1
mainline=training_dataset
sync_round_id=round_20260607_local_reverse_training_status_summary_sync_v1
sync_decision_id=decision_20260607_local_reverse_training_status_summary_sync_v1
executed_sample=false
ran_static_tools=false
ran_runtime_tools=false
updated_file=project_state\local_reverse_training_status.json
updated_sample_statuses=false
updated_known_candidates=false
before_summary={sample_count=29, solved=2, blocked=5, needs_triage=0, inventory_only=22}
after_summary={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}
computed_from_samples=true
status_overlay_summary_agrees=true
post_solve_sync_summary_agrees=true
recent_solved_sample_id=cpp2_2f64e68d
known_candidate=10013
next_queue_hint_sample_id=cpp2_32f1713e
generated_at=<timestamp>
```

### Phase E — artifact_index

Register:

```text
latest_artifacts["local_reverse_training_status_summary_sync"]
latest_artifacts_v2["local_reverse_training_status_summary_sync"]
```

`latest_artifacts_v2` must include:

```text
kind=local_reverse_training_status_summary_sync
path=project_state\local_reverse_training_status_summary_sync.json
freshness=current
source_run=round_20260607_local_reverse_training_status_summary_sync_v1
sha256=<actual sha256>
size_bytes=<actual size>
modified_at=<artifact generated_at or filesystem mtime>
sample_id=cpp2_2f64e68d
```

Do not remove existing `local_reverse_post_solve_state_sync` or `local_reverse_cpp2_2f64e68d_training_status_sync` artifacts.

### Phase F — optional low-token pointers

If useful, update `project_state/current_state.json` and `project_state/task_packet.json` by adding only low-token fields such as:

```text
local_reverse_training_status_summary_sync=project_state\local_reverse_training_status_summary_sync.json
local_reverse_training_summary_source=project_state\local_reverse_training_status.json
```

Preserve all old fields. Do not change `task_packet.task`. Do not turn `cpp2_32f1713e` into an execution task.

### Phase G — report

`codex_execution_report.md` top block must be:

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_training_status_summary_sync_v1",
  "round_id": "round_20260607_local_reverse_training_status_summary_sync_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_training_status_summary_sync_v1",
  "status": "SUCCESS|BLOCKED|FAILED",
  "acceptance_recommendation": "ACCEPTED|ACCEPTED_WITH_LIMITATIONS|REWORK_REQUIRED|BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

Report must explicitly state that this is a training status summary sync and not new solving.

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
3. local_reverse_training_status summary computed from samples[].
4. local_reverse_training_status summary updated to solved=3 blocked=4 needs_triage=0 inventory_only=22.
5. legacy count fields updated: solved_count=3 blocked_count=4 inventory_only_count=22.
6. No samples[] entry status/candidate/classification was changed.
7. status_overlay summary agrees with training_status summary.
8. post_solve_sync summary agrees with training_status summary.
9. local_reverse_training_status_summary_sync.json exists and records before/after summary.
10. artifact_index registers local_reverse_training_status_summary_sync current provenance.
11. task_packet.task remains advisory and unchanged.
12. cpp2_32f1713e remains next_queue_hint only, not executed.
13. pytest_result uses this decision_id/report_id/round_id.
14. git diff --name-status only contains allowed files.
```

---

## 8. Stop Conditions

Stop and write `status=BLOCKED` or `status=FAILED`, not ACCEPT, if any condition occurs:

```text
1. accepted oracle-backed validation artifact is missing or not VALIDATED_SUCCESS.
2. post_solve_sync artifact is missing or does not say solved=3 blocked=4.
3. status_overlay summary does not say solved=3 blocked=4.
4. recomputing local_reverse_training_status samples[] does not yield sample_count=29 solved=3 blocked=4 needs_triage=0 inventory_only=22.
5. Any samples[] entry would need status/candidate/classification mutation.
6. Any sample, IDA/Ghidra, debugger, hook, emulator, solver, bruteforce, or runtime probe would be needed.
7. current_state/task_packet update would delete old samplereverse compatibility fields.
8. task_packet.task would become cpp2_32f1713e execution task.
9. local_reverse_training_status_summary_sync.json is not generated.
10. artifact_index does not register local_reverse_training_status_summary_sync.
11. pytest_result does not include py_compile reverse_agent/project_state.py.
12. pytest_result does not match this decision/report/round.
13. lint-report after final report write fails.
14. git diff includes .venv, site-packages, DLL, EXE, sample binary, solve_reports, or .codex-skills.
```

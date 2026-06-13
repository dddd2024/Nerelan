```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_run_one_local_reverse_static_triage_v1",
  "round_id": "round_20260613_run_one_local_reverse_static_triage_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

本轮不再重复建立本地样本清单，也不再继续选择非 `samplereverse` 目标这一前置步骤。仓库已经有本地 inventory、training status overlay、queue builder 和 single-sample static triage adapter。

本轮目标：刷新或恢复 `project_state/local_reverse_evaluation_queue.json`，从队列中选择 rank=1 的非 `samplereverse` 样本，运行一次有界单样本静态 triage，生成 current metadata artifact。

本轮不解题，不生成 candidate/flag/password，不运行 runtime、debugger、solver 或 harness campaign。

## 2. Current Evidence

- `task_packet.json` 和 `current_state.json` 仍是旧 `samplereverse` sample state，不能作为当前样本权威。
- `project_state/local_reverse_inventory.json` 已存在，已经扫描到 `E:\reverse` 的本地样本 metadata。
- `training_materials/local_reverse/status_overlay.json` 已存在，显示 50 个 metadata 条目，其中 1 solved、2 blocked、1 needs_triage、46 inventory_only。
- `project_state/local_reverse_training_inventory_audit.md` 已说明下一步应从 `local_reverse_evaluation_queue.json` 选择 exactly one queue item 做 static triage，而不是批量求解。
- `reverse_agent/local_reverse_training_status.py` 已能生成 training status、evaluation queue 和 status overlay。
- `reverse_agent/local_reverse_single_sample_static_triage.py` 已能读取 queue/inventory，复用 IDA evidence collector，生成 compact triage artifact；它不执行目标二进制、不生成 candidate。
- `negative_results.json` 的禁止方向仍有效：不得回到 blind search、不得单纯扩大预算、不得提交完整运行目录、不得重复旧失败方向。
- `decision_packet.md` 是当前执行权威，`task_packet.json` 只是建议。

## 3. Do Not Do

- 不继续围绕 `samplereverse` 推进。
- 不重复实现 inventory、queue builder 或 static triage adapter。
- 不批量跑 `E:\reverse` 下所有样本。
- 不运行 solver、candidate search、runtime validation、debugger、emulator 或 harness campaign。
- 不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
- 不提交 raw sample、IDA database、debug trace 或大体积本地产物。
- 不修改 `.codex-skills/`。
- 不修改 `training_materials/`，除非本轮报告只读取它作为已有 overlay 证据。
- 不把旧 `samplereverse` artifact 当作当前样本证据。

## 4. Files To Inspect

必须读取：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `project_state/local_reverse_inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_training_inventory_audit.md`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/ida_scripts/collect_evidence.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`

可生成或更新：

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_selected_static_triage_target.json`
- `project_state/local_reverse_<selected_sample_id>_static_triage.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_run_one_local_reverse_static_triage_v1/*`

## 5. Required Audit

Codex 必须：

1. 确认当前目录是 `F:\reverse-agent`。
2. 确认 `E:\reverse` 存在。
3. 校验本 decision：status=`APPROVED`，mainline=`training_dataset`，skill active。
4. 明确记录 `task_packet.json/current_state.json` 是旧 `samplereverse` 状态，不能作为本轮样本权威。
5. 使用现有 `local_reverse_training_status.py` 生成或刷新 `project_state/local_reverse_training_status.json` 和 `project_state/local_reverse_evaluation_queue.json`。
6. 从 `local_reverse_evaluation_queue.json` 选择 rank=1 的样本作为本轮唯一 target。
7. 若 rank=1 是 `samplereverse`，停止并报告 queue 构建错误。
8. 写入 `project_state/local_reverse_selected_static_triage_target.json`，记录 selected sample_id、relative_path、sha256、queue_rank、allowed_actions、forbidden_actions。
9. 对 selected sample 运行一次 `local_reverse_single_sample_static_triage.py`。
10. triage artifact 必须是 metadata artifact，必须记录 `executed_sample=false`、`static_only=true`、`runtime_validated=false`。
11. 若 IDA 不可用、超时或无输出，记录为 static tool blocker；不得改写为样本语义失败。
12. 报告必须说明本轮输出是 one-sample static triage，不是解题结果。

## 6. Implementation Scope

允许修改或生成：

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_selected_static_triage_target.json`
- `project_state/local_reverse_<selected_sample_id>_static_triage.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_run_one_local_reverse_static_triage_v1/*`

仅当当前工具无法生成 queue 或 triage artifact 时，才允许最小修改：

- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- 对应最小测试

不允许修改：`.codex-skills/`、`training_materials/`、`solve_reports/`、`PROJECT_PROGRESS_LOG.txt`、solver 模块、harness 模块、debugger/olly scripts、IDA scripts、raw sample 文件。

## 7. Tests

必须运行并记录：

- `pwd`
- `Test-Path F:\reverse-agent`
- `Test-Path E:\reverse`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.local_reverse_training_status`
- `python -m reverse_agent.local_reverse_single_sample_static_triage --sample-id <rank1_sample_id> --queue project_state/local_reverse_evaluation_queue.json --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_<rank1_sample_id>_static_triage.json`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py tests/test_tool_capability_inventory.py -q`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `git diff --name-only`

验收标准：queue 生成成功；selected sample 不是 `samplereverse`；只处理一个 sample；static triage artifact 已生成；没有 candidate/flag/password；没有 runtime/debugger/harness/solver 运行。

## 8. Stop Conditions

必须停止并报告：

- `E:\reverse` 不存在。
- queue 生成失败或为空。
- rank=1 是 `samplereverse`。
- selected sample 无法在 inventory 中定位。
- selected sample 文件不存在。
- static triage 需要 runtime/debugger/solver 才能继续。
- IDA 工具故障但未记录为 static tool blocker。
- 实现试图批量处理多个样本。
- 实现试图把 `samplereverse` 继续作为当前目标。

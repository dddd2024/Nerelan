```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_state_refresh_active_execution_view_v1",
  "round_id": "round_20260615_project_state_refresh_active_execution_view_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

实现或验证 `project_state` 的 **active execution view / 状态刷新能力**。

目标不是推进逆向样本，而是让状态包在 Codex 每轮启动时能更明确地区分：

1. 当前执行权威：`project_state/decision_packet.md`
2. 当前 decision 是否已经被 SUCCESS report 消费
3. `task_packet.json` 是否只是 advisory/state input
4. `current_state.json` 是否只是旧 sample_state
5. historical sample artifacts 是否只是 external_state_notices
6. 下一轮是否需要生成新 decision，而不是复用已消费 decision

本轮目标是减少以后人工审计时反复解释“task_packet 是建议，不是当前任务”的成本。

## 2. Current Evidence

上一轮 `round_20260615_state_handoff_after_gate_acceptance_v1` 已经 ACCEPTED：

- `codex_execution_report.md` status 为 `SUCCESS`
- `acceptance_recommendation` 为 `ACCEPTED`
- `pytest_result.txt` 为 `PASSED`
- `final_gate_result.json` 为 `PASSED`
- `round_manifest.json` 已归档

但当前状态文件仍保留旧 sample 信息：

- `task_packet.json` 仍有 `derived_task: collect_missing_evidence`
- `task_packet.json` 仍有 `profile: samplereverse`
- `task_packet.json` 仍有 `state_scope: sample_state`
- `current_state.json` 仍有 `sample: samplereverse`
- `current_state.json` 仍有 `workflow_status: REPORT_AVAILABLE`

这些信息不能删除或伪造，但需要在状态视图中被明确降级为 historical/advisory。

## 3. Do Not Do

不要推进任何逆向样本求解。

不要运行 sample、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要修改 `.codex-skills/`。

不要清空、伪造、删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要把 `task_packet.task` 或 `task_packet.derived_task` 当作当前执行任务。

不要为了让状态“看起来干净”而删除旧 sample_state；正确做法是分类、标注、降级。

## 4. Files To Inspect

必须读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`
9. `project_state/gates/final_gate_result.json`
10. `project_state/rounds/round_20260615_state_handoff_after_gate_acceptance_v1/round_manifest.json`

重点检查：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

## 5. Required Audit

执行前确认：

1. 当前 `decision_packet.md` 是本轮 `decision_20260615_project_state_refresh_active_execution_view_v1`。
2. 上一轮 `decision_20260615_state_handoff_after_gate_acceptance_v1` 已经被 SUCCESS report 消费。
3. `task_packet.json` 只是 advisory/state input。
4. `current_state.json` 中旧 sample_state 不能当作当前执行主线。
5. `reverse-agent-iteration@v2` 来自 active registry。
6. 当前主线是 `engineering_branch`。
7. historical sample artifacts 只能作为 external_state_notices。
8. 不允许切换到 `reverse_solving`、`tool_integration` 或 `training_dataset`。

## 6. Implementation Scope

优先做小改动。

允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

必要时允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/*`

谨慎允许更新：

- `project_state/task_packet.json`
- `project_state/current_state.json`

前提是这些文件必须由明确的 `project_state build` 或等价状态刷新命令生成，不能手工伪造。

只读，不得修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块

具体要求：

1. 先审计当前 `project_state build` 是否已经支持生成 active execution view。
2. 如果已有能力，直接运行状态刷新命令并记录结果，不做源码修改。
3. 如果没有能力，只做最小工程增强：
   - 增加一个 compact active execution summary；
   - 或在 `doctor / lint-report / build` 输出中统一暴露当前执行视图字段。
4. active execution view 至少应包含：
   - `execution_authority`
   - `active_decision_id`
   - `active_round_id`
   - `decision_status`
   - `decision_execution_state`
   - `latest_success_report_id`
   - `latest_closed_round_id`
   - `task_packet_role`
   - `current_state_role`
   - `historical_artifacts_role`
   - `recommended_next_action`
5. 如果当前 decision 已被 SUCCESS report 消费，状态视图必须明确提示：
   - `recommended_next_action: generate_new_decision`
   - 或等价表达；
   - 不能提示继续执行已消费 decision。
6. 不要删除旧 sample_state；只允许标注其 role，例如：
   - `current_state_role: historical_sample_state`
   - `task_packet_role: advisory_state_input`
   - `artifact_freshness_role: historical_external_notices`

## 7. Tests

必须记录命令、stdout/stderr、exit code 到 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state build
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_state_refresh_active_execution_view_v1
```

必须新增或确认测试覆盖：

1. `decision_packet.md` 优先级高于 `task_packet.task`
2. consumed decision 不能被继续执行
3. old sample_state 在 engineering_branch 下被标注为 historical/advisory
4. missing historical sample artifacts 不会阻断 engineering_branch
5. active execution view 能稳定输出当前 decision/report/round 状态
6. active execution view 对已消费 decision 给出 generate_new_decision 或等价建议
7. 不删除、不伪造 artifact_index 中的 missing/stale 信息

## 8. Stop Conditions

如果需要运行样本、solver、runtime probe、debugger、hook、emulator、sidecar，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/` 才能继续，停止并报告 `BLOCKED`。

如果需要删除或伪造 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会让 `task_packet.task` 覆盖 `decision_packet.md`，停止并报告 `REWORK_REQUIRED`。

如果修改会让旧 sample_state 被误认为当前执行主线，停止并报告 `REWORK_REQUIRED`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。

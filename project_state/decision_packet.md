```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_state_handoff_after_gate_acceptance_v1",
  "round_id": "round_20260615_state_handoff_after_gate_acceptance_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

完成上一轮已接受工程门禁修复后的 **状态收口 / handoff 清理**。

目标不是继续改 solver，也不是推进具体逆向样本，而是确保下一轮 Codex 不会继续被旧 `task_packet.task=collect_missing_evidence`、旧 sample_state、旧 missing sample artifacts 误导。

本轮目标：

1. 确认上一轮 `round_20260615_startup_status_order_guard_rework_v1` 已经被 SUCCESS report 消费并归档。
2. 确认旧 `decision_packet.md` 已被消费，下一轮不能继续复用旧 decision。
3. 检查 `project_state` 当前输出是否能清楚表达：
   - 当前 decision 已消费；
   - 最新 accepted/closed round 是上一轮工程门禁轮次；
   - `task_packet.json` 只是 advisory/state input；
   - historical sample artifacts 对 `engineering_branch` 是 external notices，不是 blocker。
4. 若现有 `doctor / lint-report / status_summary` 对这些状态表达不清，最小修改状态汇总逻辑和测试。
5. 不推进样本、不运行 solver、不读取完整 `solve_reports/`。

## 2. Current Evidence

上一轮审计结论为 ACCEPTED：

- `codex_execution_report.md` 的 `based_on_decision_id` 匹配 `decision_20260615_startup_status_order_guard_rework_v1`；
- report status 为 `SUCCESS`；
- tests 记录为 `517 passed`；
- final gate 为 `PASSED`；
- `recommended_next_action` 为 `no_action_required`。

但当前状态仍存在 handoff 风险：

- `task_packet.json` 仍显示 `derived_task: collect_missing_evidence`；
- `task_packet.json` 仍指向 sample profile `samplereverse`；
- `current_state.json` 仍是旧 `sample_state`；
- `artifact_index.json` 中还有大量 historical sample missing artifacts。

这些不能作为下一轮执行权威，只能作为历史/外部状态说明。

## 3. Do Not Do

不要推进任何逆向样本求解。

不要运行 sample、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要修改 `.codex-skills/`。

不要清空、伪造、删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要把旧 `task_packet.task` 当作当前执行任务。

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
9. `project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/round_manifest.json`
10. `project_state/gates/final_gate_result.json`

必要时检查：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

## 5. Required Audit

执行前确认：

1. 当前 `decision_packet.md` 是 `decision_20260615_state_handoff_after_gate_acceptance_v1`。
2. `task_packet.json` 只是 advisory/state input。
3. `reverse-agent-iteration@v2` 来自 active registry。
4. 当前主线是 `engineering_branch`。
5. historical sample artifacts 只能作为 external_state_notices。
6. 本轮不得切换到 `reverse_solving`。
7. 本轮不得扩大到训练集、前端、多 agent、solver 或工具接入。

## 6. Implementation Scope

优先做 **无代码或极小代码状态收口**。

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
- `project_state/rounds/round_20260615_state_handoff_after_gate_acceptance_v1/*`

只读，不得修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块

具体要求：

1. 先运行当前状态检查，不急着改代码。
2. 检查 `doctor` / `lint-report` / `final-check` 是否已经能表达：
   - 最新 accepted round；
   - consumed decision；
   - task_packet 非权威；
   - engineering_branch 下 historical sample missing artifacts 非阻塞。
3. 如果现有输出已经清晰，允许本轮只生成 SUCCESS 报告和归档，不做源码修改。
4. 如果输出仍把旧 sample_state 表达成当前执行方向，才允许最小修改 `project_state` 状态汇总逻辑。
5. 新增测试必须覆盖：
   - consumed decision 不能被下一轮继续执行；
   - task_packet sample task 不能覆盖 decision_packet；
   - engineering_branch 下 historical sample missing artifacts 是 external notices；
   - latest accepted/closed round 能从 round manifest / final gate 中稳定读取。

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
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_state_handoff_after_gate_acceptance_v1
```

## 8. Stop Conditions

如果需要运行样本、solver、runtime probe、debugger、hook、emulator、sidecar，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/` 才能继续，停止并报告 `BLOCKED`。

如果需要删除或伪造 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果发现上一轮 archive/report/pytest_result 不匹配，停止并报告 `REWORK_REQUIRED`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。

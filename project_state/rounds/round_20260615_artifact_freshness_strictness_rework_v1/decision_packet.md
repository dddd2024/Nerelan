```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_artifact_freshness_strictness_rework_v1",
  "round_id": "round_20260615_artifact_freshness_strictness_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 artifact freshness strictness 的残留语义错误。

目标：

1. `engineering_branch` 可以把 historical sample missing/stale artifacts 作为 external_state_notices 非阻塞处理。
2. `reverse_solving / tool_integration / training_dataset` 必须严格要求 current artifact freshness。
3. `_classify_artifact_freshness()` 和 `_historical_artifact_freshness_is_non_blocking()` 的真实行为必须与 `artifact_freshness_requirement=strict` 一致。
4. 测试不得再断言 `reverse_solving` 或 `training_dataset` 的 missing/stale artifact freshness 可 non-blocking。

## 2. Current Evidence

上一轮已经修复：

- round manifest metadata；
- old manifest fallback；
- `task_packet_role=authoritative` 命名问题。

但当前代码仍在 `_historical_artifact_freshness_is_non_blocking()` 中允许 `reverse_solving` 和 `training_dataset` 走 historical artifact non-blocking 分支。该行为违反本轮 stop condition。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要把 `task_packet.task` 重新定义为执行权威。

不要把非工程主线的 missing/stale artifact freshness 改成 warning-only 或 non-blocking。

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

重点检查：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260615_project_state_mainline_clarity_rework_v2/round_manifest.json`

## 5. Required Audit

执行前确认：

1. 当前 decision 是本返工包。
2. `task_packet.json` 仍只是 advisory/state input。
3. `artifact_index.json` 仍可能包含 historical missing artifacts，但这只对 `engineering_branch` 可 non-blocking。
4. `reverse_solving / tool_integration / training_dataset` 不允许 missing/stale artifact freshness 被 `_historical_artifact_freshness_is_non_blocking()` 放行。
5. 现有 manifest metadata 修复不得回退。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

必要时允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_artifact_freshness_strictness_rework_v1/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 将 `_historical_artifact_freshness_is_non_blocking()` 的 non-blocking 主线限制为 `engineering_branch`。
2. 删除或修改允许 `reverse_solving` non-success missing/stale artifacts 返回 `True` 的分支。
3. 确认 `training_dataset` 不再通过 consumed-success path 被 non-blocking 放行。
4. 保留 `tool_integration` strict 行为。
5. 增加测试：
   - `engineering_branch` missing/stale historical artifacts non-blocking；
   - `reverse_solving` missing/stale artifacts blocking；
   - `tool_integration` missing/stale artifacts blocking；
   - `training_dataset` missing/stale artifacts blocking；
   - `status_summary()` 虽显示 `artifact_freshness_requirement=strict`，其 `artifact_freshness_blocking` 也必须为 `True`；
   - 现有 manifest metadata 和 fallback 测试继续通过。
6. 删除或反转当前 `reverse_solving` non-blocking 测试。

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_artifact_freshness_strictness_rework_v1
```

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果 `engineering_branch` 以外的主线仍能把 missing/stale artifacts 分类为 non-blocking，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。

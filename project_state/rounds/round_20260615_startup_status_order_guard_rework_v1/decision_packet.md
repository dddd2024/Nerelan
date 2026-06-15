```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_startup_status_order_guard_rework_v1",
  "round_id": "round_20260615_startup_status_order_guard_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 baseline capture order guard 的启动状态采集顺序问题。

上一轮新增的 `baseline_capture_order` 检查依赖 `pytest_result.txt` 中第一个 `git status --short` block 作为 startup dirty evidence。但实际记录中 `git status --short` 出现在 `Set-Location F:\reverse-agent` 和 `git rev-parse --show-toplevel` 之前，不能严格证明该状态来自 `F:\reverse-agent` 仓库。

本轮目标：

1. 保留 `baseline_capture_order` 检查。
2. 保留 `_extract_startup_dirty_files()` 使用第一个合格 startup git status block 的语义。
3. 将 command-plan / pytest_result 的启动顺序规范为：
   - `Set-Location F:\reverse-agent`
   - `Get-Location`
   - `Test-Path F:\reverse-agent`
   - `git rev-parse --show-toplevel`
   - `git status --short`
4. 只有在上述目录确认完成后采集的 `git status --short`，才能作为 startup dirty evidence。
5. 如果 `pytest_result.txt` 中第一个 `git status --short` 出现在路径确认之前，`startup_command_coverage` 或新增检查应 `FAIL`。
6. 不得回退上一轮 `baseline_capture_order` 的 overlap 检查、startup evidence 检查、WARN/FAIL 语义。

## 2. Current Evidence

上一轮已经实现：

- `_baseline_capture_order_checks()`；
- `_extract_startup_dirty_files()`；
- `_parse_git_status_short_dirty()`；
- final-check / close-round 集成；
- 测试 `507 passed`；
- `final_gate_result.json` 输出 `baseline_capture_order: WARN / confirmed_inherited`。

但当前问题是：

- `pytest_result.txt` 第一条命令是 `git status --short`；
- 后面才执行 `Set-Location F:\reverse-agent`、`Get-Location`、`Test-Path F:\reverse-agent`、`git rev-parse --show-toplevel`；
- 这不满足本项目启动门禁，也削弱 startup dirty evidence 的可信度。

## 3. Do Not Do

不要推进任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要回退 artifact freshness strictness 修复。

不要回退 `_NEGATION_PHRASES` / `_report_explains_inherited_baseline_files()`。

不要回退 `baseline_capture_order` 的核心判断。

不要继续把“路径确认前的 git status”当作可信 startup evidence。

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

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_baseline.json`

## 5. Required Audit

执行前确认：

1. 当前 decision 是 `decision_20260615_startup_status_order_guard_rework_v1`。
2. `task_packet.json` 仍只是 advisory/state input。
3. 当前任务来自 `project_state/decision_packet.md`，不来自 `task_packet.task`。
4. `reverse-agent-iteration@v2` 必须来自 active registry。
5. 历史 sample artifacts missing 仍只是 `engineering_branch` 下的 external_state_notices。
6. 本轮只修 startup command ordering / startup evidence validity，不推进样本。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

必要时允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_startup_status_order_guard_rework_v1/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体要求：

1. 调整 command-plan 生成顺序，使启动阶段固定为：
   1. `Set-Location F:\reverse-agent`
   2. `Get-Location`
   3. `Test-Path F:\reverse-agent`
   4. `git rev-parse --show-toplevel`
   5. `git status --short`
2. 修改 `_extract_startup_dirty_files()` 或其调用方：只有当 `git status --short` block 出现在上述路径确认命令之后，才可作为 startup dirty evidence。
3. 如果 `git status --short` 出现在 `Set-Location / Get-Location / Test-Path / git rev-parse` 之前，应返回空 evidence 或让对应 gate `FAIL`。
4. 增加 gate 检查字段，例如：
   - `startup_status_order_valid`
   - `startup_status_block_index`
   - `path_confirmation_block_indexes`
   - `startup_status_evidence_trusted`
5. `baseline_capture_order` 只能使用 trusted startup evidence。
6. 如果 startup evidence 不可信且存在 baseline/files_changed/source-test overlap，应 `FAIL`，不能降级为 confirmed inherited。
7. 保留现有 `baseline_capture_order` 测试，并新增不可信顺序测试。

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

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
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_startup_status_order_guard_rework_v1
```

必须新增或更新测试：

1. command-plan 输出顺序必须是路径确认命令在前，`git status --short` 在后。
2. `git status --short` 出现在路径确认之后：startup evidence trusted。
3. `git status --short` 出现在 `Set-Location` 前：startup evidence untrusted。
4. `git status --short` 出现在 `git rev-parse --show-toplevel` 前：startup evidence untrusted。
5. untrusted startup evidence + baseline/files_changed/source-test overlap：`baseline_capture_order` 必须 `FAIL`。
6. trusted startup evidence + overlap：仍为 `WARN / confirmed_inherited`。
7. no startup evidence + overlap：仍为 `FAIL / suspected_late_capture`。
8. `_report_explains_inherited_baseline_files()` 现有 negation guard 测试继续通过。
9. `reverse_solving / tool_integration / training_dataset` artifact freshness strictness 测试继续通过。

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果需要删除 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修改会削弱 `reverse_solving / tool_integration / training_dataset` 的 artifact freshness strictness，停止并报告 `REWORK_REQUIRED`。

如果修改会回退 `_NEGATION_PHRASES` 或 `baseline_capture_order`，停止并报告 `REWORK_REQUIRED`。

如果仍然让路径确认前的 `git status --short` 作为 startup evidence，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_decision_immutability_and_build_output_scope_guard_v1",
  "round_id": "round_20260615_decision_immutability_and_build_output_scope_guard_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 `project_state_refresh_active_execution_view_v1` 审计中暴露出的两个工程规范问题：

1. **live `project_state/decision_packet.md` 不可被 Codex 执行轮反向修改**。
2. **`project_state build` 会重写哪些动态状态文件必须有明确 scope 规则**。

本轮不是继续扩展 active execution view，也不是推进逆向样本；本轮目标是把执行边界做硬，避免以后 Codex 通过修改当前 decision 来适配 dirty baseline，或因为 `project_state build` 造成未声明状态文件漂移。

## 2. Current Evidence

上一轮 `round_20260615_project_state_refresh_active_execution_view_v1` 审计结论是 `ACCEPTED_WITH_LIMITATIONS`。

已接受部分：

- `active_execution_view()` 已实现；
- `active-execution-view` CLI 已接入；
- `pytest` 记录为 `526 passed`；
- `final_gate_result.json` 为 `PASSED`；
- round archive 已创建；
- 没有推进样本求解，也没有改 solver / strategy / IDA / Ghidra / debugger / harness。

限制点：

1. Codex 在执行过程中修改了 live `project_state/decision_packet.md`，加入 `Allowed Inherited Dirty Baseline Files` 段。该文件是当前执行权威，执行轮不应反向改写。
2. 本轮 `project_state build` 运行后改动了 `project_state/artifact_index.json`、`project_state/current_state.json`、`project_state/task_packet.json`、`project_state/model_gate.json`、`project_state/negative_results.json` 等动态状态文件；其中部分文件未在上一轮 Implementation Scope 中明确列出。
3. 报告声称验证了 active-execution-view CLI，但 `pytest_result.txt` 的 command list 没有单独记录该 CLI 命令。以后报告中声称验证的命令必须进入 `tests_ran` / `pytest_result`。

当前状态仍然保留旧 sample 信息：`samplereverse / collect_missing_evidence / sample_state`。这仍然只能作为 historical/advisory，不是当前执行主线。

## 3. Do Not Do

不要推进任何逆向样本求解。

不要运行 sample、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要修改 `.codex-skills/`。

不要清空、伪造、删除 `artifact_index.json` 中的 missing/stale historical artifacts。

不要把 `task_packet.task` 或 `task_packet.derived_task` 当作当前执行任务。

不要在执行过程中修改 live `project_state/decision_packet.md`。允许读取它；允许 `close-round` 把它复制到 `project_state/rounds/<round_id>/decision_packet.md`；不允许把 live 文件加入 `files_changed`。

不要为了压掉 baseline warnings 再给 live decision 补 allowlist。若启动时 source/test 文件已经 dirty，必须按 baseline 规则记录；若需要修改 decision 才能通过 gate，应停止并报告 `REWORK_REQUIRED`。

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
10. `project_state/rounds/round_20260615_project_state_refresh_active_execution_view_v1/round_manifest.json`

重点检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

## 5. Required Audit

执行前确认：

1. 当前 `decision_packet.md` 是本轮 `decision_20260615_decision_immutability_and_build_output_scope_guard_v1`。
2. 上一轮 `decision_20260615_project_state_refresh_active_execution_view_v1` 已经被 SUCCESS report 消费。
3. `task_packet.json` 只是 advisory/state input。
4. `current_state.json` 中旧 sample_state 不能当作当前执行主线。
5. `reverse-agent-iteration@v2` 来自 active registry。
6. 当前主线是 `engineering_branch`。
7. historical sample artifacts 只能作为 external_state_notices。
8. 不允许切换到 `reverse_solving`、`tool_integration` 或 `training_dataset`。
9. 启动 `git status --short` 如果显示 live `project_state/decision_packet.md` dirty，应停止并报告 `BLOCKED`，不能继续执行。
10. 如果报告声明某个 CLI 被验证，该 CLI 必须出现在 `codex_report_summary.tests_ran` 和 `pytest_result_summary.tests_ran`，并在 body 中有对应 command block。

## 6. Implementation Scope

优先改 gate / lint 规则和测试，不改求解逻辑。

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

必要时允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_decision_immutability_and_build_output_scope_guard_v1/*`

本轮不应运行 live `project_state build`。如果为了测试 build output scope，需要使用 pytest 临时目录 fixture，不要直接刷新 live `project_state` 动态文件。

只读，不得修改：

- live `project_state/decision_packet.md`，除本文件由 GPT 预先上传外，Codex 执行期间不得修改；
- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块。

本轮具体要求：

1. 增加或强化 gate 检查：如果 current round 的 `files_changed` 或 round delta 包含 live `project_state/decision_packet.md`，应判定为 FAIL，除非只是 archive 路径 `project_state/rounds/<round_id>/decision_packet.md`。
2. 增加或强化 gate 检查：如果 startup baseline 里 live `project_state/decision_packet.md` 已 dirty，应阻止执行，不能允许 Codex 在执行中修补当前 decision。
3. 明确 `project_state build` 的动态输出白名单，建议集中定义为：
   - `project_state/artifact_index.json`
   - `project_state/current_state.json`
   - `project_state/task_packet.json`
   - `project_state/model_gate.json`
   - `project_state/negative_results.json`
4. 如果上述 build-generated files 出现在 round delta 中，必须满足至少一个条件：
   - `pytest_result.txt` 记录了 `python -m reverse_agent.project_state build` 且 exit code 为 0；
   - 或 report 明确说明这些文件来自受控状态刷新命令，并且 command-plan / pytest_result 可验证。
5. 如果 build-generated files 出现在 round delta，但没有记录 build 命令，应 FAIL 或至少 WARN，并给出明确 `build_output_scope_unverified` 诊断。
6. 如果报告正文声称验证了某个 CLI，例如 `active-execution-view`，但该命令不在 `tests_ran` 和 command block 中，应 WARN 或 FAIL。最低要求是新增测试覆盖这一点；实现难度过高时，报告中不得再声称未记录的命令验证。
7. 不要改 active_execution_view 的业务语义，除非为测试或字段稳定性修复必要 bug。
8. 不要删除旧 sample_state；只允许标注其 role 或让 active execution view 降级解释。

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
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_decision_immutability_and_build_output_scope_guard_v1
```

必须新增或确认测试覆盖：

1. live `project_state/decision_packet.md` 出现在 current round `files_changed` 时，final-check 或 close-round 必须 FAIL。
2. archive 路径 `project_state/rounds/<round_id>/decision_packet.md` 不触发 live decision mutation failure。
3. startup baseline 中 live `project_state/decision_packet.md` dirty 时，preflight/final-check 至少有明确 blocking 诊断。
4. build-generated state files 白名单稳定输出。
5. build-generated state files 若出现在 round delta 且 pytest_result 未记录 `project_state build`，应产生 `build_output_scope_unverified` 诊断。
6. build-generated state files 若出现在 round delta 且 pytest_result 记录 build 命令 exit 0，应被分类为受控状态刷新产物。
7. 报告声称验证的 CLI 必须被 `tests_ran` / `pytest_result` 覆盖，至少对 `active-execution-view` 建一个回归测试或在报告模板中禁止未记录 claim。
8. 现有 active execution view 行为不回退：consumed decision 仍推荐 `generate_new_decision`，READY_FOR_EXECUTION 仍推荐 `execute_decision_scope`。
9. 不删除、不伪造 artifact_index 中的 missing/stale 信息。

## 8. Stop Conditions

如果需要运行样本、solver、runtime probe、debugger、hook、emulator、sidecar，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/` 才能继续，停止并报告 `BLOCKED`。

如果需要修改 live `project_state/decision_packet.md` 才能通过 gate，停止并报告 `REWORK_REQUIRED`。

如果启动时 `project_state/decision_packet.md` 已 dirty，停止并报告 `BLOCKED`，不要继续修改。

如果修改会让 `task_packet.task` 覆盖 `decision_packet.md`，停止并报告 `REWORK_REQUIRED`。

如果修改会让旧 sample_state 被误认为当前执行主线，停止并报告 `REWORK_REQUIRED`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。

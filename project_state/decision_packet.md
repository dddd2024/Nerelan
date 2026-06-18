```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_post_close_round_failure_report_reconciliation_v1",
  "round_id": "round_20260618_post_close_round_failure_report_reconciliation_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 `non_closeout_synthesis_rework_required_fix` 的收尾报告不一致问题。

上一轮源码修改和 pytest 有进展，但最终报告错误地写成 `SUCCESS/ACCEPTED`，而当前 gate evidence 显示：

- `final_gate_result.json.gate_status=FAILED`
- `report_summary_synthesis.json` 期望 `FAILED/REWORK_REQUIRED`
- `pytest_result_summary.status=SUCCESS` 被判定非法
- `close-round` 失败
- round archive 没有成功闭合

本轮目标不是继续扩展功能，而是把 report、pytest_result、gate artifacts、close-round 记录修到一致。

目标行为：

- 若 close-round 失败，报告必须是 `FAILED` 或 `PARTIAL` + `REWORK_REQUIRED`。
- 不得继续写 `SUCCESS/ACCEPTED`。
- 不得声明不存在或未成功闭合的 archive evidence。
- `report-summary` 和 `final-check` 最终不能有 FAIL。
- 已实现的 fast non-closeout source fix 不要重写，除非发现明确源码 bug。

## 2. Current Evidence

当前主线是 `engineering_branch`。

`task_packet.json` 仍是建议；当前执行权威是 live `project_state/decision_packet.md`。`task_packet.json` 也明确 `execution_scope=decision_packet_controls_current_round`。

上一轮源码和测试情况：

- 修改了 `reverse_agent/project_gate.py`
- 修改了 `tests/test_project_gate.py`
- pytest：`774 passed`

但 gate 状态不合格：

- `final_gate_result.json.gate_status=FAILED`
- `report_summary_fields_match_synthesis` 仍 FAIL
- `status_policy_valid` FAIL
- `pytest_result_match` FAIL

上一轮不能 ACCEPTED。

`current_state.json` 仍描述旧 `samplereverse` reverse-solving 状态；该状态不是本轮 engineering_branch report reconciliation 的 current evidence。

`artifact_index.json` 中多数历史 `samplereverse` artifacts 为 missing；这些历史样本 artifact 只能作为外部状态通知，不能作为本轮 current gate evidence。

`negative_results.json` 仍禁止旧 reverse-solving 方向，包括 blind old solver search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports，以及重复已失败的 `samplereverse` 分支。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 为 active 且 version=2，因此 `reverse-agent-iteration@v2` 有效。

已有工具接口审计：本轮不进入 reverse_solving/tool_integration/training_dataset，不运行 IDA/Ghidra/debugger/emulator/solver/harness。若 Codex 在执行中发现需要运行逆向工具，必须停止并报告越界。

允许读取重型 artifact：不允许默认读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。只允许读取本 decision 明确列出的 project_state gate artifact 和相关源码/测试。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sample runner 或 GUI/frontend workflow。

不要修改 solver、harness、strategy、transform、tool-runner、debugger integration、sample 文件、`.codex-skills/`、`solve_reports/`。

不要只改正文而不修 structured summary。

不要把失败的 close-round 写成成功。

不要把不存在的 round archive 文件写入 `generated_artifacts`。

不要把 `final-check` 的 FAIL 当作可接受 warning。

不要修改本 decision 文件；如果启动时本 decision 文件已 dirty，立即停止。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

重点检查：

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/command_plan.json`
6. `project_state/gates/gate_profile_plan.json`
7. `reverse_agent/project_gate.py`
8. `tests/test_project_gate.py`

只在证明源码仍有 bounded bug 时才修改源码。

不要读取无关 reverse-solving 或 tool-integration 模块，除非 gate command 明确报告某个 forbidden-path blocker 且点名相关文件。

## 5. Required Audit

修改前确认：

1. 工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向该仓库。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是 gate/report reconciliation，不是逆向样本求解。
9. 启动时没有 source/test dirty；若已有 source/test dirty，停止并报告 baseline 状态，不修改文件。

必须解释清楚：

1. 为什么上一轮 report 写成 `SUCCESS/ACCEPTED` 是错误的。
2. close-round 是否成功。
3. archive files 是否真实存在并匹配 current report/pytest。
4. `pytest_result_summary.status` 应该使用什么非成功状态。
5. `report_summary_synthesis.json` 与 `codex_report_summary` 是否最终一致。
6. `final_gate_result.json` 是否最终无 FAIL。

## 6. Implementation Scope

优先只修改 project_state/report artifacts：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`

只有在证明确有 bounded gate bug 时，才允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

要求：

1. 如果 close-round 失败，report summary 改为 `FAILED / REWORK_REQUIRED`。
2. `pytest_result_summary.status` 不得继续写非法 `SUCCESS`。
3. report body 必须说明 close-round 的真实 exit code 和失败原因。
4. 不得列出不存在的 archive files。
5. 若最终 final-check 无 FAIL 且 closeout_allowed=true，再重试 close-round。
6. 如果 close-round 仍失败，报告必须保持 `FAILED/REWORK_REQUIRED`，并停止。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_project_gate.py tests/test_project_state.py -q

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `closeout_allowed=true`：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_post_close_round_failure_report_reconciliation_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 source/test 文件被修改，必须保证 pytest 真实运行且结果写入 `project_state/pytest_result.txt`。

本轮报告必须包含：

- `codex_report_summary` fenced JSON；
- `based_on_decision_id=decision_20260618_post_close_round_failure_report_reconciliation_v1`；
- `round_id=round_20260618_post_close_round_failure_report_reconciliation_v1`；
- `files_changed`；
- `tests_ran`；
- `generated_artifacts`；
- 每个 gate command 的执行结果摘要；
- 如果 close-round 失败，必须明确说明 exit code 和 blocking reasons；
- 如果未运行 close-round，必须明确说明原因。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 启动目录不是 `F:\reverse-agent`。
2. decision 文件启动时 dirty。
3. source/test 文件启动时已有未记录 dirty。
4. `decision_meta` 缺失或不是 `APPROVED`。
5. `reverse-agent-iteration@v2` 不是 active。
6. 修复需要修改允许范围外文件。
7. 最终 report 仍写 `SUCCESS/ACCEPTED`，但 close-round 失败或 final-check 有 FAIL。
8. `pytest_result_summary.status` 仍被 gate 判定非法。
9. `report-summary` 或 `final-check` 最终仍有 FAIL。
10. archive files 不存在却被报告为 generated artifacts。
11. 报告/pytest result 的 decision_id 或 round_id 与本 decision 不匹配。

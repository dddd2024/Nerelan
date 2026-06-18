```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_gate_profile_tier_verification_v1",
  "round_id": "round_20260618_gate_profile_tier_verification_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

验证 `project_gate` 的三档 gate profile 是否都能在当前工程状态下可运行、可审计、可收尾。

本项目当前代码中的三档名称是：

- `fast`
- `standard`
- `full`

用户口中的 `medium` 对应本仓库当前实现里的 `standard`。本轮不要新增第四种 `medium` 命名，也不要把 `standard` 重命名成 `medium`。

本轮目标：

1. 证明 `fast` profile 在 artifact-only/report-only 场景下可运行，且 close-round 被正确省略。
2. 证明 `standard` profile 在普通 source/test 变更场景下可运行，且执行 targeted pytest / doctor / lint-report / report-summary / final-check，但不强制 close-round。
3. 证明 `full` profile 在 gate/project_state/harness/solver/tool-runner 等高风险路径场景下可运行，且命令计划包含 run-round、pytest、doctor、lint-report、report-summary、final-check、close-round。
4. 生成一个 gate tier verification artifact，总结三档触发条件、required_command_kinds、closeout_allowed、最终状态和限制。
5. 如果发现某一档不能闭环，不要掩盖失败；报告 `REWORK_REQUIRED`，并精确指出失败档位和 gate check。

本轮不是逆向解题，不进入训练样本求解，不运行 IDA/Ghidra/debugger/emulator。

## 2. Current Evidence

主线是 `engineering_branch`。

上一轮 `post_close_round_failure_report_reconciliation_v1` 已把报告状态从错误的 `SUCCESS/ACCEPTED` 修正为 `PARTIAL/REWORK_REQUIRED`，并且 `report-summary` 已 PASSED、`final-check` 为 WARN 且无 FAIL。当前限制是 fast non-closeout 未生成 round archive。

当前已知 gate profile 状态：

- `fast` 已在最近一轮真实 project_state 中跑通到 `final-check WARN` 且无 FAIL；`closeout_allowed=false`，`close-round` 正确省略。
- `standard` 代码路径存在，但缺少最近一轮真实验证记录。
- `full` 代码路径存在并曾被触发；上一轮涉及 `reverse_agent/project_gate.py` 时进入 full，但 close-round/报告一致性曾失败，之后通过 fast reconciliation 修正报告状态。本轮需重新验证 full profile 的计划和收尾链路，不得沿用旧失败结论。

`task_packet.json` 仍是旧 `samplereverse` reverse-solving 建议，且其 `execution_scope` 表示当前执行以 `decision_packet.md` 为准。不要把 `task_packet.task` 当成本轮执行权威。

`current_state.json` 仍描述旧 `samplereverse` reverse-solving 状态；它不是本轮 gate tier verification 的 current evidence。

`artifact_index.json` 中多数历史 reverse-solving artifacts 仍为 missing；这些只能作为外部状态通知，不得作为当前 gate tier verification 的证据。

`negative_results.json` 禁止旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports，以及重复旧 `samplereverse` 失败分支。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 为 active 且 version=2，因此 `reverse-agent-iteration@v2` 有效。

已有工具能力规则：本轮不进入 reverse_solving/tool_integration/training_dataset；不运行 IDA/Ghidra/debugger/solver/harness。若验证过程中发现需要逆向工具，立即停止并报告越界。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要把 `medium` 写入代码作为新 profile 名称；当前规范名是 `standard`。

不要为了让三档通过而降低 full profile 的 closeout/archive/manifest 要求。

不要把 WARN 说成 PASSED；报告必须区分 PASSED / WARN / FAILED。

不要把旧 round archive 或 stale `round_close_snapshot.json` 当成本轮 current evidence。

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

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py`
4. `project_state/gates/gate_profile_plan.json`
5. `project_state/gates/command_plan.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/codex_execution_report.md`
9. `project_state/pytest_result.txt`

必要时读取历史 round，只允许有界读取：

- `project_state/rounds/round_20260617_gate_profile_tier_integration_v1/*`
- 与最近 gate profile 修复直接相关的 round manifest/report/pytest

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向 `F:/reverse-agent` 或等价路径。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是 gate tier verification，不是逆向样本求解。
9. 启动时 source/test dirty 状态已记录；若存在未记录 source/test dirty，停止并报告 baseline，不修改文件。

必须审计并记录：

1. `fast` 的触发条件、required_command_kinds、closeout_allowed。
2. `standard` 的触发条件、required_command_kinds、closeout_allowed。
3. `full` 的触发条件、required_command_kinds、closeout_allowed。
4. `profile_override` 是否支持三档显式选择，以及非法 profile 是否失败。
5. command-plan 是否能按 profile 省略或要求对应命令。
6. report-summary/final-check 对 fast non-closeout 的处理是否仍保持一致。
7. full profile 是否仍保持严格 close-round/archive/manifest 要求。

如果发现某档测试只能靠 mock 通过，必须在报告里区分：

- unit-level verified
- CLI-level verified
- live project_state verified
- closeout verified

## 6. Implementation Scope

优先只增加/完善 gate profile 验证测试和 project_state artifact。

允许修改：

1. `tests/test_project_gate.py`
2. `tests/test_project_state.py`
3. `project_state/gate_profile_tier_verification.json`
4. `project_state/codex_execution_report.md`
5. `project_state/pytest_result.txt`
6. `project_state/gates/preflight_result.json`
7. `project_state/gates/gate_profile_plan.json`
8. `project_state/gates/command_plan.json`
9. `project_state/gates/report_summary_synthesis.json`
10. `project_state/gates/final_gate_result.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`
13. `project_state/rounds/round_20260618_gate_profile_tier_verification_v1/*` only if close-round actually runs and succeeds

只有在测试暴露明确 bounded bug 时，才允许小范围修改：

- `reverse_agent/project_gate.py`

不得修改其它源码模块。

建议实现方式：

1. 在 `tests/test_project_gate.py` 中补足 profile tier 回归测试：
   - artifact-only scope => `fast`
   - ordinary source/test path scope => `standard`
   - gate/project_state/harness/solver/tool-runner path scope => `full`
   - explicit override `fast/standard/full` 生效
   - invalid override 失败
   - full profile required_command_kinds 包含 `close-round`
   - standard profile required_command_kinds 不包含 `close-round`
   - fast profile `closeout_allowed=false`

2. 用 CLI 或最小 fixture 生成 `project_state/gate_profile_tier_verification.json`，至少包含：
   - `schema_version`
   - `decision_id`
   - `round_id`
   - `profiles.fast`
   - `profiles.standard`
   - `profiles.full`
   - 每档的 `trigger_fixture`、`expected_profile`、`actual_profile`、`closeout_allowed`、`required_command_kinds`、`status`
   - `overall_status`

3. 本轮 live project_state 可以按当前 decision 自然进入 `fast` 或 `standard/full`，但不要为了验证三档而污染 live decision_packet。三档验证应优先通过 unit/fixture/CLI 层完成。

4. 如果最终 live profile 是 fast，允许不运行 close-round；如果最终 live profile 是 full 且 final-check 无 FAIL，必须按 command-plan 执行 close-round。

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

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_gate_profile_tier_verification_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- 三档 profile 的 verified level：unit / CLI / live / closeout。
- 三档是否可运行。
- 哪一档仍未 closeout 验证。
- 若 `standard` 仍无法真实触发，必须说明原因并给下一轮最小复现任务。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 启动目录不是 `F:\reverse-agent`。
2. `decision_packet.md` 启动时 dirty。
3. source/test 文件启动时已有未记录 dirty。
4. `decision_meta` 缺失或不是 `APPROVED`。
5. `reverse-agent-iteration@v2` 不是 active。
6. 需要修改允许范围之外的文件。
7. 需要运行样本、debugger、IDA/Ghidra、emulator 或 runtime probe。
8. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
9. 把 `medium` 新增为第四档 profile。
10. 降低 full profile closeout/archive/manifest 严格性。
11. 测试没有真实运行或未写入 `project_state/pytest_result.txt`。
12. `report-summary` 或 `final-check` 最终出现 FAIL。
13. 报告中声称三档都可用，但 verification artifact 没有逐档证据。

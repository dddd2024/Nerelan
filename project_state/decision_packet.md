```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_non_closeout_synthesis_rework_required_fix_v1",
  "round_id": "round_20260618_non_closeout_synthesis_rework_required_fix_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `report-summary` 综合逻辑和 `final-check` 状态派生逻辑中的 fast non-closeout 冲突。

当前轮 evidence 显示：

- `gate-profile` 选择 `fast`；
- `closeout_allowed=false`；
- `close-round` 没有运行；
- 没有 current round archive；
- live report 正确写成 `PARTIAL / REWORK_REQUIRED`；
- 但 `report_summary_synthesis.json` 仍期望 `SUCCESS / ACCEPTED`，导致 `final-check` 只剩 `report_summary_fields_match_synthesis` 一个 FAIL。

目标行为：

- 当 `closeout_allowed=false` 且 `close-round` 未运行、没有 current archive evidence 时，综合器不得把当前报告派生为 `SUCCESS / ACCEPTED`。
- 对 fast non-closeout artifact/report-only round，若报告明确为 `PARTIAL / REWORK_REQUIRED`，且没有其它 core gate FAIL，则 `report-summary` 应与该状态一致。
- 不得削弱 full profile / standard profile 的 closeout、archive、manifest 要求。
- 不得把 stale `round_close_snapshot.json` 当 current closeout evidence。
- 不得修改逆向求解、solver、harness、debugger、sample、GUI/frontend、skill 文件或 solve_reports。

## 2. Current Evidence

主线是 `engineering_branch`。`task_packet.json` 仍是建议，当前执行权威是 live `project_state/decision_packet.md`。

现有报告已经正确降级为：

- `status=PARTIAL`
- `acceptance_recommendation=REWORK_REQUIRED`

但当前 `report-summary` 和 `final-check` 仍失败，原因是 synthesis 期望：

- `status=SUCCESS`
- `acceptance_recommendation=ACCEPTED`

当前 `gate_profile_plan.json` 显示：

- `profile=fast`
- `closeout_allowed=false`
- required command kinds 只有 startup / preflight / command-plan / report-summary / final-check

因此本轮不应继续尝试 artifact-only 修补报告。需要授权修改 `reverse_agent/project_gate.py` 的综合/status policy 逻辑，并补对应回归测试。

`current_state.json` 仍描述旧 `samplereverse` reverse-solving 状态；该状态不是本轮 engineering_branch closeout/synthesis 修复的 current evidence。

`artifact_index.json` 中多数历史 `samplereverse` artifacts 为 missing；这些历史样本 artifact 只能作为外部状态通知，不能作为本轮 current gate evidence。

`negative_results.json` 仍禁止旧 reverse-solving 方向，包括 blind old solver search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports，以及重复已失败的 `samplereverse` 分支。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 为 active 且 version=2，因此 `reverse-agent-iteration@v2` 有效。

已有工具接口审计：本轮不进入 reverse_solving/tool_integration/training_dataset，不运行 IDA/Ghidra/debugger/emulator/solver/harness；成熟逆向工具接口存在与否不影响本轮 gate synthesis 源码修复。若 Codex 在执行中发现需要运行逆向工具，必须停止并报告越界。

允许读取重型 artifact：不允许默认读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。只允许读取本 decision 明确列出的 project_state gate artifact 和相关源码/测试。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sample runner 或 GUI/frontend workflow。

不要修改 solver、harness、strategy、transform、tool-runner、debugger integration、sample 文件、`.codex-skills/`、`solve_reports/`。

不要通过只编辑 `codex_execution_report.md` 或 `pytest_result.txt` 来掩盖 synthesis 失败。

不要把 fast non-closeout 的放宽逻辑套到 full profile closeout 场景。

不要删除 generated-artifact checking、report-summary checking 或 final-check checking。

不要让 `SUCCESS / ACCEPTED` 在没有 current closeout/archive evidence 的 fast non-closeout round 中继续被派生。

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
8. 本轮是 gate/status synthesis 修复，不是逆向样本求解。
9. 启动时没有 source/test dirty；若已有 source/test dirty，停止并报告 baseline 状态，不修改文件。

实现前必须定位：

1. `build_report_summary_synthesis()` 如何派生 `status` / `acceptance_recommendation`。
2. `_report_status_from_gate_payload()` 如何把 WARN / historical sample notices 映射到 `SUCCESS / ACCEPTED`。
3. `fast_profile_closeout_consistency`、`closeout_allowed=false`、`close_round_omitted=true` 是否已经在 final-check payload 中可用。
4. `report-summary` 是否应在 fast non-closeout 下派生 `PARTIAL / REWORK_REQUIRED`，而不是 `SUCCESS / ACCEPTED`。

执行中必须验证：

1. 新逻辑只影响 fast non-closeout 场景。
2. full profile closeout/archive/manifest 要求没有被弱化。
3. stale `round_close_snapshot.json` 不被纳入 current generated artifacts。
4. `report-summary` 和 `final-check` 最终不再因为 `status` / `acceptance_recommendation` 派生冲突而 FAIL。
5. `codex_execution_report.md`、`pytest_result.txt`、gate artifacts 的 decision/round/report ID 一致。

## 6. Implementation Scope

允许修改：

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py`
4. `project_state/codex_execution_report.md`
5. `project_state/pytest_result.txt`
6. `project_state/gates/preflight_result.json`
7. `project_state/gates/gate_profile_plan.json`
8. `project_state/gates/command_plan.json`
9. `project_state/gates/report_summary_synthesis.json`
10. `project_state/gates/final_gate_result.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`
13. `project_state/gates/run_round_result.json` only if generated by an explicitly run allowed command
14. `project_state/gates/round_close_snapshot.json` only if close-round is actually run and produces current IDs
15. `project_state/rounds/round_20260618_non_closeout_synthesis_rework_required_fix_v1/*` only if close-round is actually run and succeeds

建议实现方向：

1. 在 synthesis/status 派生逻辑中识别 fast non-closeout 场景：
   - `gate_profile_plan.closeout_allowed=false`；
   - command plan 不包含 active `close-round`；
   - 没有 current round archive / current close snapshot；
   - final-check 中 `fast_profile_closeout_consistency` 表示 close-round omitted。

2. 该场景下：
   - synthesis expected status 应允许或派生为 `PARTIAL`；
   - synthesis expected acceptance 应允许或派生为 `REWORK_REQUIRED`；
   - 不应因为历史 sample artifact notice 或 archive-pending WARN 把报告升级成 `SUCCESS / ACCEPTED`。

3. 保持 full profile 行为：
   - 如果 closeout is required/allowed 且 archive evidence 缺失，不能被误判为 success。
   - full profile 的 close-round / manifest / archive checking 不得降级。

4. 补回归测试：
   - fast non-closeout + no close-round + no archive + report `PARTIAL / REWORK_REQUIRED` => `report-summary` 不产生 status/acceptance diff。
   - fast non-closeout 不应把 stale `round_close_snapshot.json` 纳入 current generated artifacts。
   - full profile / closeout_allowed=true 仍不得绕过 archive/manifest 要求。
   - 当前 bug 的最小复现测试：旧逻辑会期望 `SUCCESS / ACCEPTED`，新逻辑应期望 `PARTIAL / REWORK_REQUIRED`。

如果发现实现需要修改上述范围之外的文件，停止并报告 `REWORK_REQUIRED`，不要自行扩大范围。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

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

如果 `final-check` 无 FAIL 且 gate profile 允许 closeout，再运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_non_closeout_synthesis_rework_required_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 source/test 文件被修改，必须保证 pytest 真实运行且结果写入 `project_state/pytest_result.txt`。

本轮报告必须包含：

- `codex_report_summary` fenced JSON；
- `based_on_decision_id=decision_20260618_non_closeout_synthesis_rework_required_fix_v1`；
- `round_id=round_20260618_non_closeout_synthesis_rework_required_fix_v1`；
- `files_changed`；
- `tests_ran`；
- `generated_artifacts`；
- 每个 gate command 的执行结果摘要；
- 如果未运行 close-round，必须明确说明原因。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果出现以下情况：

1. 启动目录不是 `F:\reverse-agent`。
2. `decision_packet.md` 启动时已 dirty。
3. source/test 文件启动时已有未记录 dirty。
4. `decision_meta` 缺失或不是 `APPROVED`。
5. `reverse-agent-iteration@v2` 不是 active。
6. 修复需要修改允许范围外文件。
7. 修复会削弱 full profile closeout/archive/manifest 要求。
8. 修复需要触碰 reverse-solving、solver、harness、debugger、tool-runner、sample、GUI/frontend、skill 或 solve_reports。
9. 测试没有真实运行或没有写入 `project_state/pytest_result.txt`。
10. 最终 `report-summary` 或 `final-check` 仍有 FAIL。
11. 报告/pytest result 的 decision_id 或 round_id 与本 decision 不匹配。

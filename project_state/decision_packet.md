```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_startup_status_baseline_consistency_guard_v1",
  "round_id": "round_20260615_startup_status_baseline_consistency_guard_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# REWORK DECISION_PACKET

## 1. Goal

修复 `round_20260615_decision_immutability_scope_guard_rework_v1` 的证据一致性问题。

目标不是继续扩展功能，而是新增一个 gate 约束：`pytest_result.txt` 中启动阶段的 `git status --short` 输出，必须与 `round_baseline.json / round_delta_summary.json / final_gate_result.json` 中的 baseline dirty 记录一致。

本轮只做证据一致性 guard，不推进样本求解，不扩展 active execution view，不回退上一轮已实现的 decision immutability、build output scope、verified CLI coverage 和 active-execution-view command recognition。

## 2. Current Evidence

上一轮 `round_20260615_decision_immutability_scope_guard_rework_v1` 表面结果为：

- `codex_execution_report.md` 为 `SUCCESS / ACCEPTED`；
- `pytest_result.txt` 记录 `549 passed`；
- `command-plan` 已识别 `active-execution-view`，且 `plan_status` 为 `PASSED`；
- `report-summary / final-check / close-round` exit 0；
- `final_gate_result.json` 为 `PASSED`；
- archive 已完成。

但审计发现核心证据矛盾：

- `pytest_result.txt` 启动阶段的 `git status --short` 显示：
  - `M reverse_agent/project_gate.py`
  - `M tests/test_project_gate.py`
- 同一轮 report 又声明 `Inherited Baseline Dirty Files: None`；
- `final_gate_result.json` / round delta 也显示 `inherited_dirty_files: []`、`baseline_capture_order: clean`。

这三者不能同时成立。若启动 `git status --short` 已有 source/test dirty，则 baseline 不应被描述为 clean；若这些 dirty 是上一轮残留，必须被显式登记为 inherited baseline，并在 gate 中可验证。

## 3. Do Not Do

不要推进逆向样本求解。

不要运行 sample、solver、runtime probe、debugger、hook、emulator、sidecar。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness。

不要修改 `.codex-skills/`。

不要修改 live `project_state/decision_packet.md` 来补 allowlist。

不要运行 live `project_state build`。

不要把 `task_packet.task` 或 `task_packet.derived_task` 当作当前执行任务。

不要回退上一轮已实现的：

- decision immutability check；
- build output scope check；
- verified CLI coverage check；
- active-execution-view command recognition；
- command-plan `PASSED` 行为。

## 4. Files To Inspect

必须读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `project_state/gates/round_baseline.json`
9. `project_state/gates/round_delta_summary.json`
10. `project_state/gates/final_gate_result.json`
11. `.codex-skills/registry.json`

重点检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

必要时检查：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

## 5. Required Audit

执行前必须先完成启动检查，且在任何修改前记录：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
```

如果启动 `git status --short` 显示 source/test dirty，必须明确分类：

1. 如果 dirty 来自上一轮未提交改动，必须登记为 inherited baseline，并让 baseline / startup evidence 保持一致；
2. 如果 dirty 是本轮 preflight 前产生的修改，必须停止并报告 `REWORK_REQUIRED`；
3. 如果 live `project_state/decision_packet.md` dirty，立即停止并报告 `BLOCKED`。

不得在 source/test dirty 已经出现后伪造 clean baseline。

## 6. Implementation Scope

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
- `project_state/rounds/round_20260615_startup_status_baseline_consistency_guard_v1/*`

只读，不得修改：

- live `project_state/decision_packet.md`，除本文件由 GPT 预先上传外，Codex 执行期间不得修改；
- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块。

## 7. Required Fix

新增或强化 gate 检查：

1. 从 `pytest_result.txt` 中解析启动阶段 `git status --short` command block。
2. 提取该 command block 中的 dirty files。
3. 与 `project_state/gates/round_baseline.json`、`project_state/gates/round_delta_summary.json`、`project_state/gates/final_gate_result.json` 中的 baseline dirty / inherited dirty 字段对比。
4. 如果 startup `git status --short` 中有 source/test dirty files，但 baseline 记录为空，必须 FAIL。
5. 如果 startup `git status --short` 中有 `reverse_agent/project_gate.py` 或 `tests/test_project_gate.py` dirty，报告不能写 `Inherited Baseline Dirty Files: None`。
6. 如果 source/test dirty 是上一轮残留，必须被显式登记为 inherited baseline，不能伪装成 clean baseline。
7. 该检查应在 `final-check` 和 `close-round` 中可见；若实现成本低，也可在 `report-summary` synthesis 中暴露诊断。
8. 保留并复测上一轮 guard：
   - live decision mutation 仍 FAIL；
   - archive decision copy 仍允许；
   - build output scope 不回退；
   - verified CLI coverage 不回退；
   - active-execution-view command 不回到 unknown。

## 8. Tests

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_startup_status_baseline_consistency_guard_v1
```

必须新增或确认测试覆盖：

1. startup `git status --short` 有 source/test dirty，但 baseline dirty 为空时，`final-check` 或 `close-round` 必须 FAIL。
2. startup `git status --short` 有 source/test dirty，且 baseline 正确记录为 inherited dirty 时，不触发 startup/baseline 一致性错误。
3. startup `git status --short` clean，baseline clean 时 PASS。
4. live `project_state/decision_packet.md` dirty 仍然 FAIL。
5. `active-execution-view` command recognition 不回退，仍为 known command。
6. `command-plan --json` 对 active-execution-view 仍为 `PASSED`。
7. build output scope 检查不回退。
8. verified CLI coverage 检查不回退。
9. report 正文或 summary 不能声称 inherited dirty none，而 startup git status 有 source/test dirty。

## 9. Stop Conditions

如果仍出现 startup `git status --short` 与 baseline 记录不一致，不得写 `SUCCESS`。

如果 `report-summary / final-check / close-round` 任一 exit 1，不得写 `SUCCESS`。

如果需要修改 live `project_state/decision_packet.md` 才能通过，停止并报告 `REWORK_REQUIRED`。

如果启动时 live `project_state/decision_packet.md` dirty，停止并报告 `BLOCKED`。

如果修改会让 `task_packet.task` 覆盖 `decision_packet.md`，停止并报告 `REWORK_REQUIRED`。

如果修改会让旧 sample_state 被误认为当前执行主线，停止并报告 `REWORK_REQUIRED`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。

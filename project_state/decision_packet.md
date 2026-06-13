```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_local_reverse_full_pytest_debt_v1",
  "round_id": "round_20260613_local_reverse_full_pytest_debt_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

处理全量 `python -m pytest -q` 暴露的 7 个既有 `local_reverse` 测试失败。本轮只做测试债和工程闭环，不推进样本求解，不处理新样本。

## 2. Current Evidence

上一轮 gate/state 范围测试已通过，报告为 `SUCCESS` 且 `ACCEPTED_WITH_LIMITATIONS`。限制项是全量 pytest 仍有 7 个范围外 `local_reverse` 失败：6 个 forced IDA mock artifact 父目录缺失，1 个 static triage 默认 `mainline` 期望不一致。当前 `decision_packet.md` 是执行权威，`task_packet.json` 仍只是旧 `samplereverse` 建议。

## 3. Do Not Do

不运行真实 IDA，不运行样本，不生成 candidate/flag/password，不读完整历史报告目录，不改长期 skill，不修改训练材料，不扩大到训练集求解。

## 4. Files To Inspect

读取 project_state 默认文件、上一轮 report、pytest_result、相关 gate 输出，以及 `local_reverse` 相关测试和最小源码。重点查找 forced IDA mock artifact 写入路径、父目录创建逻辑、static triage 默认 `mainline` 合约。

## 5. Required Audit

Codex 必须先复现或读取全量 pytest 的 7 个失败明细，确认它们确实属于 `local_reverse` 测试债。对 6 个父目录缺失失败，判断应修测试 fixture 还是修产物写入代码。对默认 `mainline` 失败，明确合约：未传 `--mainline` 时默认不写入 `mainline`，传入时才写入。不得把失败简单标记为通过。

## 6. Implementation Scope

允许最小修改 `local_reverse` 相关测试、mock fixture、必要的产物写入辅助逻辑，以及 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`。如确需修改 `reverse_agent/local_reverse_single_sample_static_triage.py`，只能修默认 `mainline` 合约或目录创建，不得扩大功能。不得修改 skill、training materials、solve_reports。

## 7. Tests

必须记录：位置确认、git 状态、全量 `python -m pytest -q`、相关失败测试的定向 pytest、project gate preflight、doctor、lint-report、report-summary、final-check、diff 文件名。验收要求：全量 pytest 不再出现这 7 个 `local_reverse` 失败；若仍有其他失败，必须区分是否新增；报告 id 和 round id 匹配本轮。

## 8. Stop Conditions

若需要真实外部逆向工具或样本运行才能继续，停止。若失败来自缺失本地样本而无法用 mock/fixture 修复，停止并报告 BLOCKED。若需要修改长期 skill、训练材料或历史产物目录，停止。

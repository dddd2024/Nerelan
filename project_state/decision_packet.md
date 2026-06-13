```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_archive_closeout_after_gate_consistency_v1",
  "round_id": "round_20260613_archive_closeout_after_gate_consistency_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

完成上一轮 gate consistency 修复后的 archive/closeout 收尾。目标是补齐 round archive、让 report-summary synthesis 与 codex_report_summary 一致、让 final-check 从 WARN 变为 PASS，并把全量 pytest 结果记录进本轮 `pytest_result.txt`。

## 2. Current Evidence

当前 `decision_packet.md` 是执行权威，`task_packet.json` 仍是旧 `samplereverse` 建议。上一轮 `decision_20260613_closeout_gate_consistency_after_local_reverse_pytest_v1` 已把 final-check 从 FAILED 降为 WARN，blocking_reasons 为空，核心 gate/state 测试 302 passed。剩余限制项是：round manifest 缺失、archive report/pytest 与 live 文件不一致、report-summary synthesis 有 archive 路径漂移、全量 pytest 只在 report audit note 中出现而未进入本轮命令记录。

## 3. Do Not Do

不推进样本求解。不处理新样本。不修改 local_reverse 功能逻辑。不修改 harness、长期 skill、training materials、solve_reports 或 raw sample 文件。不把 WARN/FAIL gate 记录成成功。不通过删除检查或降低标准制造 PASS。

## 4. Files To Inspect

必须读取 project_state 默认文件、上一轮 decision/report/pytest_result、final_gate_result、report_summary_synthesis、round_delta_summary、round_baseline、command_plan、rounds 目录当前状态，以及 project_gate/project_state 中与 archive、report-summary、final-check、pytest_result summary 相关的最小代码和测试。

## 5. Required Audit

Codex 必须确认：上一轮功能修复已完成且不重复实现；本轮只做 archive/closeout；round_manifest 是否缺失；archive report/pytest 是否与 live 文件一致；report_summary_synthesis 的 diff 是否只来自 archive 路径或 inherited dirty 归因；全量 pytest 是否需要重新记录；当前 50 个 missing historical sample artifacts 仍只能作为历史限制项，不能当作当前失败。

## 6. Implementation Scope

允许更新或生成 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/rounds/round_20260613_archive_closeout_after_gate_consistency_v1/*`。允许最小修改 project_gate/project_state 的 archive 或 synthesis 逻辑及对应 gate/state 测试，但只有在现有命令无法完成 archive/closeout 时才允许。不得修改 local_reverse、harness、skill、training materials、solve_reports。

## 7. Tests

必须记录位置确认、git 状态、preflight、command-plan、command-plan json、全量 `python -m pytest -q --rootdir F:\reverse-agent\tests`、gate/state 定向 pytest、doctor、lint-report、report-summary、final-check、diff 文件名。验收要求：全量 pytest 通过；doctor/lint-report 不能失败；report-summary 不能失败；final-check 应为 PASS；round_manifest 和归档 report/pytest/decision 必须存在并被 generated_artifacts 覆盖；codex_report_summary 必须与 synthesis 一致。

## 8. Stop Conditions

若全量 pytest 出现新增失败，停止。若 archive 命令或 archive 逻辑不可用且需要大范围重构，停止。若 final-check 仍为 WARN/FAIL 且无法归因，停止。若需要修改 local_reverse、harness、skill、training materials、solve_reports 或 raw sample 文件，停止。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_closeout_gate_consistency_after_local_reverse_pytest_v1",
  "round_id": "round_20260613_closeout_gate_consistency_after_local_reverse_pytest_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

关闭 `decision_20260613_local_reverse_full_pytest_debt_v1` 的状态一致性问题。全量 pytest 已通过，不重复修 `local_reverse` 测试债。本轮只修 report-summary、final-check、command_plan、round archive、pytest_result 状态一致性。

## 2. Current Evidence

上一轮功能目标基本完成：定向 `local_reverse` 测试通过，全量 pytest 从失败变成 `1264 passed, 1 skipped, 0 failed`。但工程闭环仍失败：doctor/report-summary/final-check 记录过失败命令，pytest_result_summary 却写成 PASSED；final-check 为 FAILED；command_plan 覆盖不完整；report_summary synthesis 与 codex_report_summary 不一致；round archive 缺失；forbidden path 检测到了 inherited baseline dirty file。

## 3. Do Not Do

不继续修改 `local_reverse` 功能逻辑，除非只是验证无新增失败。不推进样本求解。不处理新样本。不修改长期 skill、训练材料或历史产物目录。不把失败 gate 记录成成功。不通过删除检查、跳过命令或降低标准制造通过结果。

## 4. Files To Inspect

必须读取 project_state 默认文件、上一轮 decision/report/pytest_result、preflight_result、report_summary_synthesis、final_gate_result、round_delta_summary、round_baseline、command_plan，以及 project_gate/project_state 中与 command plan、report summary、final check、round archive、pytest_result summary 相关的最小代码和测试。

## 5. Required Audit

确认当前 decision 是执行权威；确认上一轮全量 pytest 已通过，不重复修测试债；确认 `pytest_result.txt` 中存在失败 gate 命令但 summary 写 PASSED 的不一致；确认 final-check 的 blocking_reasons；确认 forbidden path 是否来自 inherited baseline dirty 而非本轮修改；确认 command_plan 与 tests_ran 的命令归一化差异；确认 round archive 是否缺少 manifest 或归档文件。

## 6. Implementation Scope

允许最小修改 project gate/state 逻辑、对应 gate/state 测试、project_state 报告和 gate 派生产物。允许更新 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/rounds/round_20260613_closeout_gate_consistency_after_local_reverse_pytest_v1/*`。

不得修改 `reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、`reverse_agent/local_reverse_single_sample_static_triage.py`、local_reverse 相关测试、harness、skill、training materials、solve_reports。若必须越界，停止并报告 BLOCKED。

## 7. Tests

必须记录：位置确认、git 状态、preflight、command-plan、command-plan json、全量 pytest、doctor、lint-report、report-summary、final-check、diff 文件名。验收要求：全量 pytest 通过；doctor/lint-report 不失败；report-summary 不失败；final-check 不失败；command_plan 覆盖 report 和 pytest_result 的必跑命令；pytest_result summary 不得在存在失败必跑命令时写 PASSED；codex_report_summary 必须与 gate synthesis 一致；round archive 必须存在并被 generated_artifacts 覆盖。

## 8. Stop Conditions

若全量 pytest 出现新增失败，停止。若 final-check 仍失败且无法归因，停止。若需要重新修改 local_reverse 功能逻辑、skill、training materials 或 solve_reports，停止。若 command_plan/report_summary/final_check 的失败需要扩大到无关重构，停止。

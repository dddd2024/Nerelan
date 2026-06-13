```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_static_tool_blocker_validation_rework_v1",
  "round_id": "round_20260613_static_tool_blocker_validation_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

完成上一轮 `COMPLETED_WITH_LIMITATIONS` 的返工闭环。上一轮已经定位并修复 IDA 输出目录问题：`local_reverse_single_sample_static_triage.py` 将 IDA 输出目录从 `project_state/triage_{sample_id}` 改到 `tempfile.gettempdir()/reverse_agent_triage_{sample_id}`。本轮目标是验证该修复是否真的让 `affine_8cfebe03` 产生 IDA evidence JSON；若仍失败，生成明确的 current blocker diagnostic artifact。同步修正 report status、补齐 round archive，让 final-check 不再停留在 WARN。

## 2. Current Evidence

当前执行权威是 `project_state/decision_packet.md`，不是旧 `task_packet.json/current_state.json`。上一轮报告为 `FAILED/REWORK_REQUIRED`，但截图和报告说明已完成 blocker 根因诊断：IDA 的 `GetDiskFreeSpaceEx` 无法解析 `F:\reverse-agent\project_state\triage_affine_8cfebe03` 的 NTFS 8.3 短路径，误报磁盘空间为 0，导致数据库写入失败，IDAPython 脚本未执行。源码修复已完成，但 IDA 尚未重新运行验证修复效果；round archive 未执行；report status 仍被上一轮 final_gate_result 派生为 FAILED。

## 3. Do Not Do

不运行 solver。不生成 candidate、flag、password。不运行 runtime validation、debugger、emulator、hook 或 harness campaign。不处理新样本。不修改 `.codex-skills/`、training materials、solve_reports 或 raw sample 文件。不把 IDA 仍失败伪装成成功。不把本轮扩展成 `affineenc_333f8ca9` 或其他样本分析。

## 4. Files To Inspect

必须读取 project_state 默认文件、上一轮 report、pytest_result、final_gate_result、round_delta_summary、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、`local_reverse_training_status.json`、`artifact_index.json`、`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、现有 IDA evidence collector、相关 static triage/forced IDA/xref 测试、project_state/project_gate 测试。

## 5. Required Audit

Codex 必须确认：当前 decision 合法且 skill active；上一轮源码修复已存在，不重复实现；`reverse_agent/local_reverse_single_sample_static_triage.py` 若本轮未再修改，应作为 baseline 归因，不得漏报真实变更；旧 `task_packet/current_state` 是 `samplereverse` 历史状态；`affine_8cfebe03` 当前 artifact 仍记录 `STATIC_TOOL_NO_OUTPUT`；本轮的核心验证是重跑静态 extraction smoke，而不是解题。若 IDA 不可用，必须记录工具路径、返回码、日志摘要、expected/actual artifact path 和 next action。

## 6. Implementation Scope

优先不改源码，只做验证、artifact 更新和报告闭环。允许更新或生成 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、必要的 `artifact_index.json` 登记、`project_state/rounds/round_20260613_static_tool_blocker_validation_rework_v1/*`。只有发现上一轮 temp 输出目录修复仍有小型 bug 时，才允许最小修改 static triage/forced IDA adapter 及对应测试。

不得修改 solver、harness campaign、debugger scripts、skill、training materials、solve_reports 历史目录或 raw sample 文件。

## 7. Tests

必须记录：位置确认、git 状态、preflight、command-plan、command-plan json、`tests/test_local_reverse_single_sample_static_triage.py`、`tests/test_local_reverse_forced_ida_extract.py`、`tests/test_local_reverse_xref_disassembly.py`、`tests/test_project_gate.py`、`tests/test_project_state.py`、IDA static extraction smoke for `affine_8cfebe03`、doctor、lint-report、report-summary、final-check、diff 文件名。验收要求：相关测试通过；如果 IDA evidence JSON 生成成功，登记 artifact 并更新报告为 tool blocker resolved；如果仍失败，生成 current blocker diagnostic artifact，报告必须是 `BLOCKED` 或 `ACCEPTED_WITH_LIMITATIONS`，不能写 solved/successful extraction。

## 8. Stop Conditions

若需要 runtime/debugger/solver/harness 才能继续，停止。若 IDA/Ghidra 不可用且无法通过现有 mock/diagnostic 继续，停止并报告 BLOCKED。若需要修改 skill、training materials、solve_reports 或 raw sample 文件，停止。若 final-check 仍为 WARN/FAIL 且无法归因，停止并给出下一轮 closeout 计划。

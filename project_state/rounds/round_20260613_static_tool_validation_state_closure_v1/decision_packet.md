```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_static_tool_validation_state_closure_v1",
  "round_id": "round_20260613_static_tool_validation_state_closure_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

关闭 `affine_8cfebe03` IDA static extraction validation 的状态不一致问题。IDA smoke 已成功，不重复修输出目录，不继续样本求解。本轮只做 report、pytest_result、artifact_index、gate、round archive 的一致性闭环。

## 2. Current Evidence

当前执行权威是 `project_state/decision_packet.md`，不是旧 `task_packet.json/current_state.json`。上一轮已经验证 IDA static extraction smoke 成功：`affine_8cfebe03` 生成 `ida_evidence.json`，约 82596 bytes，包含 50 strings、30 functions、1 compare context。`project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json` 已记录旧 blocker 根因、修复方式和 `blocker_status=RESOLVED`。但当前状态仍不一致：report status 写成 FAILED/REWORK_REQUIRED，pytest_result header 写 FAILED，artifact_index 仍指向旧 blocker artifact，final-check 仍为 WARN。

## 3. Do Not Do

不重新修改 IDA 输出目录逻辑。不运行 solver。不生成 candidate、flag、password。不运行 runtime validation、debugger、emulator、hook 或 harness campaign。不处理新样本。不修改 `.codex-skills/`、training materials、solve_reports 或 raw sample 文件。不把本轮扩展成 `affineenc_333f8ca9` 或其他样本分析。

## 4. Files To Inspect

必须读取 project_state 默认文件、上一轮 report、pytest_result、final_gate_result、report_summary_synthesis、round_delta_summary、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、`project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`、`artifact_index.json`、`local_reverse_training_status.json`、相关 static triage/forced IDA/xref 测试、project_state/project_gate 测试。

## 5. Required Audit

Codex 必须确认：当前 decision 合法且 skill active；IDA smoke 已成功，不重复修源码；diagnostic artifact 要保留；`local_reverse_affine_8cfebe03_static_triage.json` 已从 `STATIC_TOOL_NO_OUTPUT` 变成 success；artifact_index 是否仍指向旧 artifact；pytest_result header 与命令体是否不一致；report status 是否被旧 final gate/synthesis 派生成 FAILED；final-check WARN 是否仅来自状态字段不一致而非工具验证失败。

## 6. Implementation Scope

允许更新 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/artifact_index.json`、`project_state/gates/*.json`、`project_state/rounds/round_20260613_static_tool_validation_state_closure_v1/*`。允许重新运行并记录 static triage / forced IDA / xref 定向 pytest、project gate/state pytest、以及 IDA static extraction smoke；若已能用现有 artifact 证明，也可只做状态同步和 gate 重跑。

不得修改 `reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、solver、harness campaign、debugger scripts、skill、training materials、solve_reports 历史目录或 raw sample 文件。

## 7. Tests

必须记录：位置确认、git 状态、preflight、command-plan、command-plan json、static triage / forced IDA / xref 定向 pytest、project_gate/project_state 定向 pytest、IDA static extraction smoke for `affine_8cfebe03` 或明确引用本轮 current evidence、doctor、lint-report、report-summary、final-check、close-round/archive、diff 文件名。验收要求：相关测试通过；report status 与实际验证结果一致；pytest_result header 不得写 FAILED；artifact_index 指向本轮 success artifact；final-check 不再显示 report status 为 FAILED；round archive 存在。

## 8. Stop Conditions

如果 IDA smoke 重新运行失败，停止并把状态改为 BLOCKED 或 ACCEPTED_WITH_LIMITATIONS，不能写成功。若需要 runtime/debugger/solver/harness 或新样本分析，停止。若需要修改 skill、training materials、solve_reports 或 raw sample 文件，停止。若 final-check 仍为 WARN/FAIL 且无法归因，停止并给出下一轮 closeout 计划。

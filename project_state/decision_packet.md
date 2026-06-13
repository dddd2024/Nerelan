```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_static_tool_blocker_triage_v1",
  "round_id": "round_20260613_static_tool_blocker_triage_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

解决 local_reverse 静态工具链的当前 blocker：`affine_8cfebe03` 的 one-sample static triage 已记录 `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。本轮目标是审计现有 IDA/static extraction 接口、定位无 evidence JSON 的原因，并生成可审计的 tool blocker 诊断或最小修复。不要直接推进新样本求解。

## 2. Current Evidence

上一轮 archive/closeout 已完成，final-check 无 blocking reasons，全量 pytest 已记录通过。当前 `task_packet.json/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为历史线索，不能作为本轮执行权威。`local_reverse_training_status.json` 显示 65 个样本：1 solved、2 blocked、2 needs_triage、60 inventory_only；其中 `affine_8cfebe03` 两个路径条目均为 `needs_triage`，blocked_reason 为 `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`。`local_reverse_evaluation_queue.json` 的 rank 1 是 `affineenc_333f8ca9`，但在解决静态工具输出问题前，不应盲目推进下一个样本。

现有相关能力必须优先复用：`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、IDA evidence collector、project_state artifact 登记和 gate/report 机制。不得新建重复 IDA/Ghidra/debugger/solver/harness 接口。

## 3. Do Not Do

不运行 solver。不生成 candidate、flag、password。不运行 runtime validation、debugger、emulator、hook 或 harness campaign。不处理新样本求解。不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。不修改 `.codex-skills/`、training materials、solve_reports 或 raw sample 文件。不把 IDA 无输出伪装成样本语义失败。不重复实现已有工具接口。

## 4. Files To Inspect

必须读取：project_state 默认文件、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、`project_state/local_reverse_training_status.json`、`project_state/local_reverse_evaluation_queue.json`、`project_state/local_reverse_inventory.json`、`project_state/artifact_index.json`、`reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、现有 IDA evidence 脚本、project_state/project_gate 相关报告逻辑，以及对应测试。

## 5. Required Audit

Codex 必须确认：当前 decision 是执行权威；上一轮 archive 已完成，不再继续 gate closeout；`task_packet/current_state` 是旧 sample_state；`affine_8cfebe03` 的 static triage artifact 是 current evidence；无 evidence JSON 是工具输出 blocker，不是样本求解失败；已有 IDA/static extraction 能力是否被正确调用；输出路径父目录、预期 artifact 路径、工具返回码、日志记录、artifact_index 登记是否一致；如果 IDA 不可用，必须记录为 tool unavailable，并给出后续 fallback 决策建议。

## 6. Implementation Scope

允许最小修改 static tool adapter、forced IDA extraction、artifact 路径/父目录创建、tool blocker 诊断记录、相关 tests，以及 project_state 报告文件。允许生成或更新 `project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/static_tool_blocker_diagnostic*.json`、必要的 artifact_index 登记、round archive。

不得修改 local_reverse 训练样本内容、solver、harness campaign、debugger scripts、skill、training materials、solve_reports 历史目录。不得把本轮扩展成 affineenc 新样本分析；最多只可读取 queue 作为下一步候选线索。

## 7. Tests

必须记录位置确认、git 状态、preflight、command-plan、相关 static tool 单元测试、local_reverse forced IDA/xref/static triage 定向测试、project_state/project_gate 定向测试、doctor、lint-report、report-summary、final-check、diff 文件名。若执行静态工具 smoke，只允许静态 extraction，不允许运行样本或 runtime probe。验收要求：相关测试通过；若修复工具输出，则生成 current diagnostic/evidence artifact 并登记；若工具仍不可用，则生成明确 blocker artifact，不能写 SUCCESS_SOLVED。

## 8. Stop Conditions

若需要运行 runtime/debugger/solver/harness 才能继续，停止。若需要修改 skill、training materials、solve_reports 或 raw sample 文件，停止。若 IDA/Ghidra 等外部工具不可用且无法通过现有 mock/diagnostic 继续，停止并报告 BLOCKED。若发现必须重新设计工具接口而非最小修复，停止并给出下一轮专门 tool_integration 计划。

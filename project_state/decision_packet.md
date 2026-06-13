```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_affine_static_evidence_classification_v1",
  "round_id": "round_20260613_affine_static_evidence_classification_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

基于当前已成功的 `affine_8cfebe03` IDA 静态证据，完成一次有界静态证据结构化和训练状态更新。目标是把 `STATIC_TOOL_NO_OUTPUT` 历史 blocker 从 training status 中移除，记录当前 IDA evidence 的分类、证据来源和下一步 solver-selection 建议；不求解样本，不生成 candidate。

## 2. Current Evidence

当前 `decision_packet.md` 是执行权威，`task_packet.json/current_state.json` 仍是旧 `samplereverse` sample_state，只能作背景。上一轮 gate/status policy 已验收为 ACCEPTED_WITH_LIMITATIONS，核心 gate 已无 blocking reasons。`artifact_index.json` 中 `local_reverse_affine_8cfebe03_static_triage` 已是 current，指向 `project_state/local_reverse_affine_8cfebe03_static_triage.json`，size 22282，sha256 `1d79d992...`，source_run 为 `round_20260613_static_tool_blocker_validation_rework_v1`。`local_reverse_training_status.json` 仍把 `affine_8cfebe03` 两个重复路径条目标为 `needs_triage`，blocked_reason 仍是 `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`，这已经与当前 successful IDA evidence 不一致。

已有相关能力必须优先复用：local reverse inventory/status 生成逻辑、artifact_index、static triage artifact、diagnostic artifact、project_state gate/report 机制。不得新建重复 IDA/Ghidra/debugger/solver/harness 接口。

## 3. Do Not Do

不运行 solver。不生成 candidate、flag、password。不运行 runtime validation、debugger、emulator、hook 或 harness campaign。不处理 `affineenc_333f8ca9` 或其他新样本。不读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。不修改 `.codex-skills/`、training materials、solve_reports 或 raw sample 文件。不把静态分类写成 solved。

## 4. Files To Inspect

必须读取 project_state 默认文件、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、`project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`、`project_state/local_reverse_training_status.json`、`project_state/local_reverse_inventory.json`、`project_state/local_reverse_evaluation_queue.json`、`project_state/artifact_index.json`，以及 local_reverse training/status 相关源码和测试。只在必要时读取 IDA evidence collector 或 static triage adapter 的最小代码；不要重跑 IDA，除非当前 artifact 缺失或不一致。

## 5. Required Audit

Codex 必须确认：当前 decision 合法且 skill active；`affine_8cfebe03` 的 current static triage artifact 是成功 artifact，不再是 blocker artifact；diagnostic artifact 保留且 blocker_status 为 RESOLVED；training_status 中两个 `affine_8cfebe03` 路径条目仍有历史 blocker，需要同步；status vocabulary 是否已有适合静态 triage 完成但未 solved 的状态。如果没有安全状态枚举，优先只更新 blocked_reason、classification、evidence_sources、next_action，并在报告中说明未改 training_status 的理由。

## 6. Implementation Scope

允许生成或更新 `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`、`project_state/local_reverse_training_status.json`、`project_state/local_reverse_evaluation_queue.json`、`project_state/artifact_index.json`、`project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/rounds/round_20260613_affine_static_evidence_classification_v1/*`。允许最小修改 local_reverse training/status 生成代码和对应测试，用于正确消费 successful static triage artifact。

不得修改 IDA 输出目录逻辑、static triage extraction 逻辑、solver、harness campaign、debugger scripts、skill、training materials、solve_reports 历史目录或 raw sample 文件。不得把本轮扩展为 solve affine 或分析 affineenc。

## 7. Tests

必须记录：位置确认、git 状态、preflight、command-plan、command-plan json、local_reverse training/status 相关定向 pytest、project_gate/project_state 定向 pytest、doctor、lint-report、report-summary、final-check、close-round/archive、diff 文件名。若新增 evidence summary artifact，必须测试或人工校验其 schema、sample_id、source artifact、classification、next_action、no candidate 字段。验收要求：`affine_8cfebe03` 两个 training status 条目不再显示 `STATIC_TOOL_NO_OUTPUT` blocker；artifact_index 登记新的 evidence summary 或确认已有 current artifact；report/pytest/final-check 匹配本轮；不得新增测试失败。

## 8. Stop Conditions

若需要 runtime/debugger/solver/harness 才能继续，停止。若当前 static triage artifact 缺失、不匹配或 artifact_index 指向 stale artifact，停止并报告 BLOCKED。若需要修改 skill、training materials、solve_reports 或 raw sample 文件，停止。若训练状态枚举不支持 triaged/static-evidence-ready 且需要大范围重构，停止并报告设计建议。

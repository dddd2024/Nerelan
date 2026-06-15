```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_samplereverse_bounded_evidence_reanchor_v1",
  "round_id": "round_20260615_samplereverse_bounded_evidence_reanchor_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
}
```

# DECISION_PACKET

## 1. Goal

对 `samplereverse` 做一轮**有界证据重锚定**，目标是把当前可用证据、缺失证据、已有工具能力和下一步可执行的最小证据采集动作写清楚。

本轮不是继续搜索 candidate，也不是扩大 solver 预算。核心产物应是一个当前轮可审计的 evidence gap / reanchor artifact，用来决定后续是否运行已有 IDA / OllyDbg / harness 接口补齐 `runtime_validation`、`case_results`、`frontier_summary`、`strata_summary`、`summary` 等缺失项。

## 2. Current Evidence

当前执行权威是本 `project_state/decision_packet.md`，不是 `project_state/task_packet.json`。`task_packet.json` 只能作为建议；其当前建议是 `collect_missing_evidence`，并且列出 `case_results`、`frontier_summary`、`runtime_validation`、`strata_summary`、`summary` 缺失。

上一轮 `decision_20260615_gate_true_clean_start_validation_rework_v1` 已审计为 `ACCEPTED_WITH_LIMITATIONS`：clean-start gate validation 通过，但限制是历史样本 artifact 仍有 50 项 missing。该结论只证明工程门禁闭环有效，不证明样本证据已经恢复。

`current_state.json` 当前仍指向 `samplereverse` / `CompareAwareSearchStrategy`，`known_transform` 为 `input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix`，但 `best_candidates` 为空，`review_status=PENDING_REVIEW`，并且多个 latest runtime/static artifact 字段为空。

`artifact_index.json` 的 `latest_artifacts_v2` 对当前样本的大量 compare / runtime / harness artifact 标记为 `missing`。这些 `missing` artifact 不能当 current 证据，只能作为后续采集目标。

`negative_results.json` 必须遵守：不得回到 old `sample_solver` blind search；不得只扩大 guided_pool beam/budget；不得把 `compare_semantics_agree=false` candidate 当 primary frontier；不得提交完整 `solve_reports/`；不得重复已失败的 exact2 basin value-pool、H1/H3 fixed contrast set、无新增 runtime evidence 的 5-candidate transform trace consistency audit。

已有工具能力必须复用，不能重复造轮子：

- IDA / IDAPython：已有 `tool_runners.py`、`ida_scripts/`、IDA JSON evidence 解析和 artifact freshness 规则，状态为 implemented。
- Ghidra：当前 inventory 标记为 missing；本轮不得临时新建 Ghidra runner。
- OllyDbg / debugger：已有 `tool_runners.py`、`ollydbg_preflight.py`、`olly_scripts/` 和 runtime compare/probe 产物通道，状态为 implemented。
- solver templates：已有 `sample_solver.py`、`local_reverse_solver_profiles.py`、`local_reverse_string_solver.py`、`samplereverse_z3.py`、`advanced_solvers.py`，不得重复实现。
- harness：已有 `harness.py`、harness CLI、case result / artifact manifest / run manifest / summary 产物通道，状态为 implemented。
- artifact_index 与 StructuredEvidence：已有 freshness tracking 和 StructuredEvidence 数据结构/解析通道。

本轮允许有界读取当前仓库和 project_state；不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只有当 artifact_index 明确指向某个当前相关的小型 artifact，并且本轮需要确认其 schema/freshness 时，才允许有界读取该 artifact。

## 3. Do Not Do

不得修改 `.codex-skills/`。

不得提交完整 `solve_reports/`。

不得运行 old `sample_solver` blind search。

不得只扩大 beam、topN、budget、timeout。

不得把 stale、missing、unknown artifact 当 current 证据。

不得重复 `negative_results.json` 中已记录的失败方向，除非报告中明确写出新增证据和重试理由。

不得新建重复的 IDA / Ghidra / OllyDbg / debugger / harness / solver 接口。

不得新增 Ghidra runner；当前 Ghidra 能力缺失只能记录为能力缺口。

不得运行动态调试、runtime probe、hook、emulator 或样本执行，除非本轮先完成只读 evidence reanchor，并且现有接口、命令、输入、输出路径、budget、artifact_index 登记方式都已在报告中明确；默认不运行。

不得把本轮产物写入长期 skill。

## 4. Files To Inspect

必须按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

必须有界读取：

- `reverse_agent/tool_capability_inventory.py`
- `reverse_agent/tool_runners.py`
- `reverse_agent/evidence.py`
- `reverse_agent/harness.py`
- 与 `samplereverse` 直接相关、且已在 artifact_index 或当前源码中被引用的 solver/profile/strategy 文件
- `tests/` 中与本轮触达模块对应的测试

只有在 artifact_index 显示 current/freshness 可确认时，才允许读取对应 artifact 内容；missing/stale artifact 只能读取索引元数据，不得当作当前样本证据。

## 5. Required Audit

启动后第一组命令必须是：

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`

如果工作目录不是 `F:\reverse-agent`，或者不是该仓库，立即停止并写入 `codex_execution_report.md`：`status=BLOCKED`，`acceptance_recommendation=BLOCKED`。

如果启动时已有 dirty files，必须先记录 baseline，不得把 inherited dirty 当成本轮修改。

必须执行只读能力核验：

- 确认 IDA / IDAPython 入口是否已经存在；
- 确认 OllyDbg / debugger 入口是否已经存在；
- 确认 harness、solver templates、artifact_index、StructuredEvidence 入口是否已经存在；
- 明确 Ghidra 当前是否缺失；
- 明确哪些能力不得重复实现。

必须输出一个新的有界 evidence reanchor artifact，建议路径：

- `project_state/samplereverse_bounded_evidence_reanchor_v1.json`

该 artifact 至少包含：

- `decision_id`
- `round_id`
- `sample`
- `mainline`
- `artifact_freshness_summary`
- `missing_evidence`
- `negative_results_respected`
- `existing_tool_capabilities`
- `current_evidence_usable`
- `stale_or_missing_not_used`
- `recommended_next_action`
- `allowed_next_commands`
- `stop_reason_if_no_safe_action`

## 6. Implementation Scope

默认不修改源码。

允许生成或更新：

- `project_state/samplereverse_bounded_evidence_reanchor_v1.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_samplereverse_bounded_evidence_reanchor_v1/*`

只有发现现有 project_state / gate 代码无法登记本轮只读 reanchor artifact，且问题根因在工程代码层时，才允许小范围修改：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- 对应测试文件

若修改源码，必须在 `files_changed` 中列出，并重新运行相关 pytest。不得修改 sample solver、strategy、IDA/OllyDbg/harness 接口逻辑来绕过证据缺失。

## 7. Tests

必须记录并运行：

- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`

若未改源码，至少运行与状态/门禁相关的 pytest：

- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`

若修改源码，必须运行对应新增/修改测试以及：

- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`

完成后必须运行：

- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_samplereverse_bounded_evidence_reanchor_v1`

`project_state/pytest_result.txt` 必须记录上述命令、stdout/stderr、exit code，并且 summary 中的 decision_id/report_id/round_id 必须匹配本轮。

## 8. Stop Conditions

如果无法确认当前工作目录为 `F:\reverse-agent`，停止。

如果 `decision_meta` 解析失败、status 不是 `APPROVED`、mainline 不合法、skill_profiles 不在 registry 中，停止。

如果发现本轮需要运行动态调试、runtime probe、hook、emulator 或样本执行，但无法明确现有接口、命令、输入、输出路径、budget 和 artifact_index 登记方式，停止并把 `recommended_next_action` 写成下一轮独立 tool run decision。

如果 artifact_index 只有 missing/stale artifact，且没有安全的 current evidence 可用，不得猜 candidate；只输出 evidence gap / reanchor artifact。

如果触碰了 `.codex-skills/`、完整 `solve_reports/`、无关 solver/strategy 重写、或重复 negative_results 失败方向，报告 `REWORK_REQUIRED`。

如果 pytest_result 缺失、不匹配当前 decision/report/round，或 final gate FAILED，报告 `REWORK_REQUIRED`。

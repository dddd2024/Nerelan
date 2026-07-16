# Closeout Order Provenance Rework Plan

## Status

```text
Document type: ROADMAP_PROPOSAL
Mainline: project_governance
Audit outcome that triggered this plan: REWORK_REQUIRED
Execution authority: NO
Current task authority remains: project_state/decision_packet.md
```

本文件记录对 `decision_20260710_post_closeout_required_audit_truth_rework_v1` 的独立审计后形成的返工计划。它只用于后续决策生成，不替代当前 `project_state/decision_packet.md`，也不授权 Codex、Runner 或其他执行器立即修改代码。

## 1. Problem Statement

当前实现已经通过 pytest、final-check 和 closeout，但审计发现 closeout 生命周期的运行事实、综合执行日志与 final gate 声明存在矛盾：

1. 原始 `pytest_result.txt` 和 `execution_log.json` 记录的外层命令顺序为：

   ```text
   execution-log
   -> close-round
   -> run-closeout
   ```

2. `final_gate_result.json` 同时声称 `close-round` 是最后命令。
3. `round_manifest.json` 的归档时间早于最终 `run_closeout_result.json` 的生成时间。
4. 报告中的 `report_finalization` 依赖最终 `run_closeout_result.json`，但当前证据不足以证明报告最终化后又执行了最终归档刷新。
5. Required Audit 第 25、26 项主要引用代码路径和设计顺序，没有引用足够的运行时 provenance 字段。

因此，当前问题不是功能未实现，而是最终 truth chain 无法无歧义证明：

```text
closeout evidence exists
-> report finalized from observed evidence
-> final archive refreshed
-> archived report equals final live report
```

## 2. Goal

建立唯一、可观测、可验证的 canonical closeout 生命周期，使以下事实能够由 artifact 字段直接证明，而不是由实现说明推断：

```text
1. run-closeout evidence 已产生；
2. final report 基于该 evidence 完成最终化；
3. report-summary、execution-log、final-check 已基于最终报告刷新；
4. final close-round/archive refresh 在报告最终化之后执行；
5. 归档报告、pytest、decision 和 manifest 与最终 live artifact 一致；
6. final gate 对命令顺序的声明与原始执行记录一致。
```

## 3. Existing Foundation

已有基础能力不得重复实现：

- `project_gate` hard gates；
- command-plan authority；
- execution-log synthesis；
- report-summary synthesis；
- run-closeout 与 close-round；
- round archive 与 round manifest；
- report alias parity；
- state-manifest freshness；
- post-final evidence sync；
- Required Audit future-claim 检查；
- Required Audit live metadata claim 检查；
- report-finalization block；
- final report/archive parity 检查。

本轮只能补强这些已有机制的顺序和 provenance，不得建立第二套 closeout 框架。

## 4. Proposed Decision Identity

后续正式 DECISION_PACKET 建议使用：

```text
decision_id: decision_20260716_closeout_order_provenance_rework_v1
round_id: round_20260716_closeout_order_provenance_rework_v1
mainline: project_governance
```

正式 decision 必须在执行前基于当时最新的 state build ID 和 digest 重新生成，不能直接复制本文件作为执行权威。

## 5. Implementation Scope

### 5.1 Canonical Closeout Lifecycle

建立单一生命周期：

```text
startup and baseline
-> implementation and tests
-> preliminary report generation
-> preliminary validation
-> generate stable run-closeout evidence
-> finalize report from observed run-closeout evidence
-> refresh report-summary
-> refresh execution-log
-> refresh final-check
-> final close-round/archive refresh
-> final live/archive parity verification
-> post-final context sync
```

不得再允许外层执行器自由组合 `close-round` 与 `run-closeout` 的先后顺序。

### 5.2 Command Ordering Truth

- `pytest_result.txt` 保留真实执行顺序；
- `execution_log.json` 必须保持原始时间顺序，不得为了匹配 command-plan 而重排；
- `final-check` 中关于最后命令的结论必须直接来自原始 transcript；
- 若 `pytest_result`、`execution_log` 与 `final_gate_result` 对顺序的描述不一致，必须 hard fail；
- command-plan 可定义覆盖要求和 expected exit codes，但不能覆盖实际时间事实。

### 5.3 Report Finalization Provenance

为 report finalization 增加或确保存在可审计字段：

```text
report_finalized_at
report_finalization_basis
run_closeout_result_path
run_closeout_result_sha256
run_closeout_generated_at
run_closeout_status
embedded_close_round_status
```

Required Audit 必须引用这些实际 artifact 字段，而不是只描述函数调用关系。

### 5.4 Final Archive Refresh Provenance

`round_manifest.json` 或等价 closeout artifact 应记录：

```text
report_finalized_at
archive_refreshed_at
archive_refresh_basis
archived_report_sha256
live_report_sha256_at_archive
final_archive_refresh_status
```

强制条件：

```text
archive_refreshed_at >= report_finalized_at
archived_report_sha256 == live_report_sha256_at_archive
```

如果 report finalization 后没有发生最终 archive refresh，closeout 必须失败。

### 5.5 Required Audit Truth

Required Audit 第 25、26 项至少引用：

- `run_closeout_result.json.generated_at`；
- `report_finalization.report_finalized_at`；
- `round_manifest.archive_refreshed_at`；
- 最终 archived/live report digest parity；
- 对应 artifact 路径。

禁止只使用以下类型的证据：

```text
“代码按该顺序调用”
“设计要求第六步执行 close-round”
“函数会在另一个函数之后运行”
```

## 6. Candidate Files To Inspect

正式 decision 应先审查以下文件，再确定最小允许修改范围：

```text
reverse_agent/project_gate.py
reverse_agent/project_state.py

tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_state.py

project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/run_closeout_result.json
project_state/gates/final_gate_result.json
project_state/gates/report_summary_synthesis.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/<current_round>/round_manifest.json
```

不得默认扩大到前端、Runner、Job、数据库或其他主线。

## 7. Required Tests

至少新增以下回归测试：

1. `pytest_result` 中 `close-round` 出现在最终 `run-closeout` 之前时，生命周期校验失败。
2. `execution_log` 最后命令与 `final_gate_result` 声明不一致时失败。
3. `round_manifest.archived_at` 或 `archive_refreshed_at` 早于 `report_finalized_at` 时失败。
4. report finalization 后未执行 final archive refresh 时失败。
5. archived report digest 与最终 live report digest 不一致时失败。
6. Required Audit 第 25、26 项只引用实现说明、没有运行 artifact 字段时失败。
7. `execution_log` 合成不得改变原始 transcript 顺序。
8. report alias finalization 字段不一致时失败。
9. 正确顺序能够通过：

   ```text
   stable closeout evidence
   -> report finalization
   -> summary/log/final-check refresh
   -> final close-round/archive refresh
   -> parity verification
   ```

10. 保留现有 state-manifest freshness、report alias parity、future claim rejection 和 live metadata claim tests。

## 8. Do Not Do

本返工计划不得用于实施以下工作：

```text
Goal / Plan / Task Contract
Scheduler
多工作线状态命名空间
独立 Code Review Plane
前端调度平台
LangChain 或 LangGraph 接入
真实 Agent Runner dispatch
数据库、队列或远程执行
逆向样本求解
工具接入
cleanup apply
```

这些方向必须等待本返工轮获得 `ACCEPTED` 或 `ACCEPTED_WITH_LIMITATIONS` 后，再进入各自 workstream 和独立 decision。

## 9. Stop Conditions

出现以下情况立即停止并报告，不得自行扩大范围：

1. 必须重写整个 `project_gate.py` 才能完成；
2. 必须改变 decision_packet 作为唯一任务权威的规则；
3. 必须放宽 command-plan 授权才能让测试通过；
4. 必须删除历史 round 或修改旧审计记录；
5. 必须修改 frontend、Runner、Job、CI workflow 或数据库；
6. 无法用 artifact 字段证明 report finalization 与 archive refresh 的先后关系；
7. 修复导致现有 state-manifest freshness 或 report alias parity 回归。

## 10. Acceptance Criteria

仅在以下条件全部满足时接受：

```text
- decision/report/pytest/command-plan/execution-log/final-gate/manifest ID 一致；
- pytest 完整通过；
- 无未授权命令；
- 无 forbidden path 修改；
- execution_log 保持真实顺序；
- final gate 的顺序结论与原始 transcript 一致；
- report_finalized_at 有当前运行证据；
- archive_refreshed_at 晚于或等于 report_finalized_at；
- final archived report 与 final live report digest 相同；
- Required Audit 第 25、26 项引用当前 artifact 字段；
- final-check 通过；
- closeout 通过；
- 独立审计结论为 ACCEPTED 或 ACCEPTED_WITH_LIMITATIONS。
```

## 11. Follow-up Sequence

该返工轮通过后，再按以下顺序推进新架构：

```text
1. 注册 multi_workstream_control_plane 与 independent_code_review workstreams；
2. Goal / Plan / Task Contract Foundation；
3. Independent Code Review Foundation；
4. ExecutionContext 与 workstream-scoped state namespace；
5. Scheduler dry-run；
6. Goal/Plan 前端；
7. Workspace Manager；
8. Local deterministic runner；
9. Codex adapter；
10. Integration Queue。
```

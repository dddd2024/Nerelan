```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_affine_audit_closure_rework_v1",
  "round_id": "round_20260613_affine_audit_closure_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

返工 `decision_20260613_affine_audit_closure_v1` 的审计闭环。目标不是继续分析 affine 样本，而是修复当前 gate/preflight/report-summary/final-check/round archive 不闭合的问题，使本轮报告、pytest_result、gate artifacts、round manifest 一致。

本轮仅处理工程审计闭环：让 `preflight_result.json`、`report_summary_synthesis.json`、`final_gate_result.json`、`round_manifest.json`、`codex_execution_report.md`、`pytest_result.txt` 对齐当前 `decision_20260613_affine_audit_closure_rework_v1`。不得继续样本求解，不改变 affine 静态证据语义。

## 2. Current Evidence

当前主线为 `engineering_branch`，因为本轮目标是 project_state/gate/report/round archive 的工程一致性修复，不是 reverse_solving、tool_integration 或 training_dataset 内容推进。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景和状态一致性问题线索，不能覆盖本 decision。不得处理 samplereverse missing artifacts。

上一轮 `decision_20260613_affine_audit_closure_v1` 的核心 affine 证据核验通过，但审计闭环失败：`preflight_result.json` 为 FAILED；`report_summary_synthesis.json` 为 FAILED；`final_gate_result.json` 不是当前 round；当前 round manifest 缺失。`pytest_result.txt` 中 doctor 最终为 WARN，但 lint-report、report-summary 没有在 report/pytest 更新后重新通过。

`codex_execution_report.md` 当前基于 `decision_20260613_affine_audit_closure_v1`，报告状态为 SUCCESS，但它自己记录的 limitation 包括 preflight FAIL、doctor/lint-report 初始 FAIL、round archive 缺失。由于该 decision 的 Stop Conditions 明确要求无法生成真实 final-check/round archive 记录时不得报告 SUCCESS/ACCEPTED，因此本轮必须返工。

`artifact_index.json` 中 `local_reverse_affine_8cfebe03_static_triage` 与 `local_reverse_affine_8cfebe03_static_evidence_summary` 均为 current；大量旧 `samplereverse` runtime/search artifacts 仍为 missing，不能作为 affine 当前证据，也不应在本轮修复。

`local_reverse_affine_8cfebe03_static_evidence_summary.json` 仍显示 `candidate=null`、`known_candidate=""`、`no_candidate=true`。`local_reverse_training_status.json` 中两个 `affine_8cfebe03` 条目仍为 `needs_triage`，`known_candidate` 为空，`blocked_reason` 为空。本轮必须保持这些语义不变。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

已存在相关能力必须优先复用：project_gate preflight/command-plan/report-summary/final-check/close-round，project_state doctor/lint-report，round_manifest 归档机制，codex_execution_report/pytest_result schema。不得重写已有 gate/report/round 机制；若 gate parser 对 Do Not Modify 路径误判，优先做最小修复或调整 decision 文本避免误判。

涉及逆向工具边界：本轮不运行 IDA/Ghidra/debugger/emulator/harness，不新增工具接口，不重跑静态 triage。已有 IDA 静态证据只用于核对 provenance，不用于生成新 candidate。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、上一轮 affine 静态 summary/triage/diagnostic、gate/round 文件和最小相关源码/测试。

## 3. Do Not Do

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得重新运行 IDA/Ghidra，不得新增或修改 IDA/Ghidra/debugger/solver/harness/static triage extraction 逻辑。

不得生成 candidate、flag、password，或把 `affine_8cfebe03` 标成 solved。

不得修改 `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的 candidate、known_candidate、no_candidate、classification、source artifact、source_tool、tool_status 等语义字段。

不得修改 `project_state/local_reverse_training_status.json` 中 affine 的 solved/candidate 状态。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports，不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得把 preflight/report-summary/final-check 的 FAIL 简单写成“false positive”后继续成功；必须让 gate artifacts 与报告状态一致，或者把报告标记为 REWORK_REQUIRED/BLOCKED。

不得把旧 `samplereverse` missing artifacts 当作 affine 当前证据，也不得为了修复旧 `samplereverse` 状态而扩大本轮范围。

## 4. Files To Inspect

必须按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

还必须有界读取：

- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`（若存在）
- `project_state/gates/command_plan.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/rounds/round_20260613_affine_audit_closure_v1/*`（若存在）
- `project_state/rounds/round_20260613_affine_audit_closure_rework_v1/*`（若存在）
- `reverse_agent/project_gate.py`、`reverse_agent/project_state.py`、round/report/doctor/lint 相关最小源码
- 与 project_gate/project_state/doctor/lint 直接相关的测试

## 5. Required Audit

Codex 必须确认并修复或如实报告：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 只是旧 `samplereverse` 背景，当前执行权威是本 decision。
- `preflight_result.json` 不能保留 blocking FAIL 后仍报告 SUCCESS。
- `report_summary_synthesis.json` 不能保留 FAILED 后仍报告 SUCCESS。
- `final_gate_result.json` 必须是当前 `round_20260613_affine_audit_closure_rework_v1`，不能沿用旧 round。
- 必须生成当前 round 的 `round_manifest.json`，并归档本轮 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt`。
- 如果 gate parser 确实误判 Do Not Modify 路径，应做最小修复或调整 decision 文本让 parser 不误判；不能只在报告中声明“误报”。
- report-summary、doctor、lint-report 必须在 report/pytest 更新后重新运行，并记录最终结果。
- `affine_8cfebe03` 两个 training status 条目仍为 `needs_triage`，`known_candidate` 为空，`blocked_reason` 为空，不被误改为 solved。
- `local_reverse_affine_8cfebe03_static_evidence_summary` 仍保持 `candidate=null`、`known_candidate=""`、`no_candidate=true`。
- 若最终仍有 FAIL，`codex_execution_report.md` 必须标记 REWORK_REQUIRED 或 BLOCKED，不得标记 SUCCESS。

## 6. Implementation Scope

允许生成或更新以下文件，且只用于审计闭环：

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_affine_audit_closure_rework_v1/*`
- `project_state/artifact_index.json`（仅当需要登记本轮 audit/round artifact，不能改 affine evidence summary 的语义）

允许最小修改以下源码和测试，仅限于修复 gate parser 误判、final-check/report-summary/close-round 不一致、或 doctor/lint-report 对当前 round 的状态识别问题：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- 与 project_gate/project_state 直接相关的测试

若无需改源码，优先不改源码。

不得修改：

- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的语义字段
- `project_state/local_reverse_training_status.json` 中 affine 的 solved/candidate 状态
- IDA/Ghidra/debugger/solver/harness/static triage extraction 逻辑
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件

## 7. Tests

必须运行并记录：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state` 或项目中实际等价命令
- `python -m reverse_agent.project_gate close-round --state-dir project_state` 或项目中实际等价命令
- 脚本或人工核验：affine 仍未 solved，candidate 为空，summary 仍 `no_candidate=true`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_affine_audit_closure_rework_v1`、`round_20260613_affine_audit_closure_rework_v1`、真实命令、退出码和测试结果。不能只记录“先失败，后来口头说明已解决”。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_affine_audit_closure_rework_v1`，`round_id=round_20260613_affine_audit_closure_rework_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

验收要求：preflight、doctor、lint-report、report-summary、final-check、close-round/archive 的最终状态必须与报告一致；若有无法消除的 WARN，必须明确写入 limitations。若存在 FAIL，不得报告 SUCCESS。

## 8. Stop Conditions

如果无法让 preflight/report-summary/final-check/round archive 形成一致闭环，停止并报告 BLOCKED 或 REWORK_REQUIRED。

如果需要运行 solver、runtime validation、debugger、emulator、hook、harness campaign、IDA/Ghidra，停止。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果需要改变 affine evidence summary、training status solved/candidate、或任何样本求解结论，停止。

如果 gate/doctor/lint 失败来自本轮之外的大范围历史缺陷，只记录为 limitation，不扩大范围修复；除非失败直接阻断本轮 audit closure rework 的最小记录生成。

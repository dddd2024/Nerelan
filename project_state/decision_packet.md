```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_affine_audit_closure_v1",
  "round_id": "round_20260613_affine_audit_closure_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

补齐上一轮 `decision_20260613_affine_static_evidence_classification_v1` 的工程审计闭环。上一轮核心实现已达到 `ACCEPTED_WITH_LIMITATIONS`：`affine_8cfebe03` 静态证据 summary、training status 同步、artifact_index 登记和 pytest/verify_round 均已完成；限制点是缺少完整 gate/doctor/lint/report-summary/final-check/round archive/git diff 记录。本轮只做审计记录、round 归档和状态闭环，不继续样本求解，不改变 affine 的候选、分类或 solver 结论。

## 2. Current Evidence

当前主线为 `engineering_branch`，原因是本轮目标是 project_state/gate/round/report 审计闭环，不是 reverse_solving、tool_integration 或 training_dataset 内容推进。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景和状态一致性问题线索，不能覆盖本 decision。

上一轮报告 `project_state/codex_execution_report.md` 声明 `decision_20260613_affine_static_evidence_classification_v1` 执行成功，mainline 为 `training_dataset`，未生成 candidate，未运行 runtime/debugger/emulator/harness，修改范围集中在 `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`、`project_state/local_reverse_training_status.json`、`project_state/artifact_index.json`、`project_state/codex_execution_report.md`、`project_state/pytest_result.txt`。

上一轮 `project_state/pytest_result.txt` 记录同一 decision/report/round，`tests/test_project_state.py` 与 `tests/test_project_gate.py` 共 302 passed，`evidence_summary_schema_validation` 通过，`verify_round.py` 通过。

`artifact_index.json` 中 `local_reverse_affine_8cfebe03_static_triage` 与 `local_reverse_affine_8cfebe03_static_evidence_summary` 均为 current；大量旧 `samplereverse` runtime/search artifacts 仍为 missing，不能作为 affine 当前证据，也不应在本轮修复。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

已存在相关能力必须优先复用：project_state 默认文件、project_gate/preflight/final-check/report-summary/close-round、doctor/lint、round_manifest、git diff 归档、codex_execution_report/pytest_result schema。不得重写已有 gate/report/round 机制。

涉及逆向工具边界：本轮不运行 IDA/Ghidra/debugger/emulator/harness，不新增工具接口，不重跑静态 triage。已有 IDA 静态证据只用于核对 provenance，不用于生成新 candidate。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、上一轮 affine 静态 summary/triage/diagnostic、gate/round 文件和最小相关源码/测试。

## 3. Do Not Do

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得生成 candidate、flag、password，或把 `affine_8cfebe03` 标成 solved。

不得修改 IDA/Ghidra/debugger/solver/harness 接口，不得修改 static triage extraction 逻辑，不得重新分析 `affineenc_333f8ca9` 或其他新样本。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports， 不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得把旧 `samplereverse` missing artifacts 当作 affine 当前证据，也不得为了修复旧 `samplereverse` 状态而扩大本轮范围。

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

还必须有界读取：

- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
- `project_state/local_reverse_affine_8cfebe03_static_triage.json`
- `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/gates/*.json`（若存在）
- `project_state/rounds/round_20260613_affine_static_evidence_classification_v1/*`（若存在）
- `reverse_agent/project_gate.py`、project_state/round/report/doctor/lint 相关最小源码
- 与 project_gate/project_state/doctor/lint 直接相关的测试

## 5. Required Audit

Codex 必须确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- 上一轮 `codex_report_summary.based_on_decision_id` 与 `pytest_result_summary.decision_id` 均指向 `decision_20260613_affine_static_evidence_classification_v1`。
- 上一轮核心产物仍存在：static evidence summary、training status、artifact_index entry、pytest_result。
- `affine_8cfebe03` 两个 training status 条目仍为 `needs_triage`，`blocked_reason` 为空，classification/evidence_sources/next_action 保留，不被误改为 solved。
- `local_reverse_affine_8cfebe03_static_evidence_summary` 的 artifact_index freshness 为 current，source_run 为 `round_20260613_affine_static_evidence_classification_v1`。
- 本轮只补齐 gate/doctor/lint/report-summary/final-check/round archive/git diff 记录；不得改变上一轮静态证据语义。
- 若发现已有 close-round/archive 产物已存在且合法，只记录核验结果，不重复生成冲突 archive。

## 6. Implementation Scope

允许生成或更新以下文件，且只用于审计闭环：

- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_affine_audit_closure_v1/*`
- `project_state/rounds/round_20260613_affine_static_evidence_classification_v1/*` 中缺失的 archive 文件（仅当工具机制要求补齐上一轮归档，且不得改写上一轮核心事实）
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/artifact_index.json`（仅当需要登记本轮 audit/round artifact，不能改 affine evidence summary 的语义）

允许最小修改 project_gate/project_state/doctor/lint/report 相关源码或测试，仅限于修复“审计闭环记录缺失但核心结果已完成”的工程记录问题。若无需改源码，优先不改源码。

不得修改：

- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的分类、candidate、no_candidate、source artifact 等语义字段
- `project_state/local_reverse_training_status.json` 中 affine 的 solved/candidate 状态
- IDA/Ghidra/debugger/solver/harness/static triage extraction 逻辑
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件

## 7. Tests

必须运行并记录：

- 位置确认：`Get-Location`、`Test-Path F:\reverse-agent`、`git status --short`
- decision preflight / command-plan / command-plan json（使用项目已有 gate 命令）
- project_state/project_gate 定向测试：至少 `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`，必要时附带 ignore 损坏 git 备份目录参数
- doctor 或项目现有等价健康检查
- lint-report 或项目现有等价 lint 检查
- report-summary
- final-check
- close-round/archive
- git diff 文件名清单，并归档到 round manifest 或对应报告
- 人工/脚本核验：affine 两个 training status 条目未变成 solved，candidate 仍为空，evidence summary 仍 `no_candidate=true`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_affine_audit_closure_v1`、`round_20260613_affine_audit_closure_v1`、真实命令、退出码和测试结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_affine_audit_closure_v1`，`round_id=round_20260613_affine_audit_closure_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

## 8. Stop Conditions

若需要运行 solver、runtime/debugger/emulator/harness、重新执行 IDA/Ghidra 才能继续，停止并报告 BLOCKED。

若需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止并报告 BLOCKED。

若发现上一轮 affine static evidence summary、training status 或 artifact_index 已缺失/不一致，停止并报告 REWORK_REQUIRED，不要自行求解或重建样本证据。

若 gate/doctor/lint 失败来自本轮之外的大范围历史缺陷，只记录为 limitation，不扩大范围修复；除非失败直接阻断本轮 audit closure 的最小记录生成。

若无法生成真实测试/doctor/lint/final-check/round archive 记录，不得报告 SUCCESS/ACCEPTED，必须在 codex_execution_report 中标记 REWORK_REQUIRED 或 BLOCKED，并说明缺失项。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_gate_closure_framework_fix_v1",
  "round_id": "round_20260613_gate_closure_framework_fix_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 gate 框架闭环问题，使 `report-summary`、`final-check`、`close-round` 能在同一轮内形成一致、可归档、可验收的工程闭环。本轮不是 affine 样本分析，也不是训练集推进；只处理 project_gate/project_state 的报告合成、命令覆盖、exit code 校验、round archive 生命周期问题。

上轮 `decision_20260613_affine_audit_closure_rework_v1` 已确认：preflight 已从失败修复为全 PASS，doctor/lint-report/pytest 基础检查可运行，上一轮 affine 产物完整性也通过；但 `report-summary`、`final-check`、`close-round` 仍因循环依赖和记录不一致失败。因此本轮目标是做最小框架修复，让 gate 命令链可闭合。

## 2. Current Evidence

当前主线为 `engineering_branch`。理由：本轮处理的是 gate/report/archive 框架行为，不属于 reverse_solving、tool_integration、training_dataset。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景，不能覆盖本 decision。不得修复或推进 `samplereverse` missing artifacts。

上轮 `decision_20260613_affine_audit_closure_rework_v1` 的 `codex_execution_report.md` 已如实标记 `status=FAILED`、`acceptance_recommendation=REWORK_REQUIRED`，并指出阻塞来自 gate 框架闭环：`report-summary` 根据 `pytest_result` 中自身及后续 gate 的失败 exit code 推导 FAILED；`final-check` 要求 report-summary 通过；`close-round` 又要求 final-check 通过，从而形成循环依赖。

上轮 `pytest_result.txt` 记录：preflight PASSED，command-plan PASSED，302 pytest passed，doctor WARN，lint-report OK；但 final `report-summary` FAILED，final-check FAILED，close-round FAILED。close-round 的 BLOCK 包括 `command_plan_covers_report_tests`、`pytest_result_exit_codes_match_command_plan`、`generated_artifacts_cover_round_archive`。

上轮 `project_state/gates/final_gate_result.json` 仍为 FAILED，blocking reasons 包括：

- command_plan 覆盖不完整，`verify_audit.py` 出现在 report/pytest 但不在 command_plan；
- pytest_result 记录的命令块与 command_plan 期望不匹配；
- report_summary_fields_match_synthesis 失败；
- round_manifest 缺失，archive 未完成。

上轮 `project_state/gates/report_summary_synthesis.json` 为 FAILED，expected 包含 round archive 文件，而 actual 没有 `project_state/rounds/round_20260613_affine_audit_closure_rework_v1/*`。

`artifact_index.json` 中 `local_reverse_affine_8cfebe03_static_triage` 与 `local_reverse_affine_8cfebe03_static_evidence_summary` 均为 current；大量旧 `samplereverse` artifacts 仍为 missing，不能作为当前证据，也不得在本轮修复。

`negative_results.json` 禁止旧 sample_solver 盲搜、扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

已有相关能力必须优先复用：project_gate preflight/command-plan/report-summary/final-check/close-round，project_state doctor/lint-report，round_manifest 归档机制，codex_execution_report/pytest_result schema。目标是修复现有框架闭环，不新建重复 gate 系统。

涉及逆向工具边界：本轮不运行 IDA/Ghidra/debugger/emulator/harness，不新增工具接口，不重跑静态 triage。已有 IDA 静态证据只用于核对不被破坏，不用于生成 candidate。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state/gates、round 文件、report/pytest、最小 project_gate/project_state 源码和测试。

## 3. Do Not Do

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得运行 IDA/Ghidra，不得新增或修改 IDA/Ghidra/debugger/solver/harness/static triage extraction 逻辑。

不得生成 candidate、flag、password，或把 `affine_8cfebe03` 标成 solved。

不得修改 `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` 的 candidate、known_candidate、no_candidate、classification、source artifact、source_tool、tool_status 等语义字段。

不得修改 `project_state/local_reverse_training_status.json` 中 affine 的 solved/candidate 状态。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports，不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得用手工伪造 gate 通过结果替代框架修复。若仍存在 FAIL，报告必须标记 FAILED/REWORK_REQUIRED/BLOCKED，不能写 SUCCESS/ACCEPTED。

不得把旧 `samplereverse` missing artifacts 当作当前工程失败主因；这些只能作为非阻塞历史 artifact limitation。

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
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260613_affine_audit_closure_rework_v1/*`（若存在）
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json`
- `project_state/local_reverse_training_status.json`
- `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- 与 project_gate/project_state 直接相关的测试，尤其 `tests/test_project_gate.py`、`tests/test_project_state.py`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景；当前执行权威是本 decision。
- 上轮 preflight 已 PASS，不再重复修 affine audit decision 文本本身，除非为了测试 fixture 必要。
- 上轮失败的真实根因是 gate framework 闭环和命令记录规则，而不是 affine 证据错误。

必须定位并最小修复：

- `report-summary` 是否错误地把自身命令、final-check、close-round 的临时失败 exit code 作为合成 status 的决定性失败；
- `command_plan_covers_report_tests` 是否应允许明确声明的额外 verification 命令，或要求 command-plan 生成时包含这些 extra checks；
- `pytest_result_exit_codes_match_command_plan` 对 PowerShell 命令、带注释后缀命令、final/report/close 多阶段命令的匹配是否过严；
- `close-round` 对 archive 文件的校验是否存在先有 archive 才能 archive 的循环；
- `report-summary`、`final-check`、`close-round` 的执行顺序是否需要两阶段状态：pre-archive summary、post-archive summary，或允许 close-round 生成 archive 后再刷新 final summary。

必须保证最终行为：

- 若所有核心检查通过且只有历史 sample artifacts missing，则允许 PASS_WITH_LIMITATIONS/WARN，但不能 FAIL；
- 若 round archive 尚未创建，close-round 应能创建 archive，而不是因 archive 文件未在 report generated_artifacts 中预先存在而阻塞；
- final-check 应校验当前 round 的 `final_gate_result.json`，不得沿用旧 round；
- report-summary 与 codex_report_summary 的 files_changed/tests_ran/generated_artifacts 规则必须可由同一轮真实命令记录满足；
- 如果额外 verify 命令被允许，规则必须明确、测试覆盖，并在 command-plan 或报告校验中保持一致。

还必须确认 affine 产物未被破坏：

- `affine_8cfebe03` 两个 training status 条目仍为 `needs_triage`，`known_candidate` 为空，`blocked_reason` 为空；
- `local_reverse_affine_8cfebe03_static_evidence_summary` 仍保持 `candidate=null`、`known_candidate=""`、`no_candidate=true`；
- 不运行 solver/runtime/debugger/IDA/Ghidra。

## 6. Implementation Scope

Allowed

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_gate_closure_framework_fix_v1/*`
- `project_state/artifact_index.json` only if needed to register current audit/round artifacts, without changing affine evidence semantics

禁止

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
- targeted pytest for changed gate behavior, including new or updated tests that reproduce the previous circular dependency and archive bootstrap failure
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260613_gate_closure_framework_fix_v1` 或项目实际等价命令
- close-round 后重新运行 `doctor`、`lint-report`、`report-summary`、`final-check`，确认 archive 后状态一致
- 脚本或人工核验：affine 仍未 solved，candidate 为空，summary 仍 `no_candidate=true`

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_gate_closure_framework_fix_v1`、`round_20260613_gate_closure_framework_fix_v1`、真实命令、退出码和最终结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_gate_closure_framework_fix_v1`，`round_id=round_20260613_gate_closure_framework_fix_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

验收要求：preflight、doctor、lint-report、report-summary、final-check、close-round/archive 的最终状态必须与报告一致。若仍存在 FAIL，报告必须为 FAILED/REWORK_REQUIRED/BLOCKED；不得报告 SUCCESS。

## 8. Stop Conditions

若需要运行 solver、runtime validation、debugger、emulator、hook、harness campaign、IDA/Ghidra，停止。

若需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

若需要改变 affine evidence summary、training status solved/candidate、或任何样本求解结论，停止。

若 gate 框架修复需要大范围重构，停止并报告设计建议；本轮只允许最小闭环修复。

若无法让 report-summary/final-check/close-round/archive 形成一致闭环，停止并报告 BLOCKED 或 REWORK_REQUIRED，不能把失败包装为 SUCCESS。

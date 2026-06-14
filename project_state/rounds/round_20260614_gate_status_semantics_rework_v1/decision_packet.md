```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_gate_status_semantics_rework_v1",
  "round_id": "round_20260614_gate_status_semantics_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复当前工程状态闸门中的 report/gate 状态语义不一致问题，使 `codex_report_summary`、`project_state/gates/report_summary_synthesis.json`、`project_state/gates/final_gate_result.json`、`pytest_result.txt` 中的 CLI 输出和 round archive 对同一轮执行给出一致、可审计、不可误读的状态结论。

本轮主线是 `engineering_branch`。目标是状态机、报告合成、final gate、测试和 round closeout 合约修复；不是 `reverse_solving`，不是 `tool_integration`，不是继续求解或重跑 `cpp1_2f6fcb63`。

本轮成功标准：当 `report_summary_synthesis.json` 判定 synthesized summary 与 `codex_report_summary` 不一致时，系统必须给出一致的非通过语义，或者要求 Codex 把 report summary 调整到合成状态；不得出现 CLI 显示 `final-check: PASSED`、但 `final_gate_result.json` 为 `WARN`，同时 report 仍写 `SUCCESS/ACCEPTED_WITH_LIMITATIONS` 的矛盾组合。

## 2. Current Evidence

上一轮审计结论为 `ACCEPTED_WITH_LIMITATIONS`：`cpp1_2f6fcb63` 的 IDA 静态 triage 工具链已经成功，artifact 为 current，且未运行样本、未生成 candidate、未标记 solved。因此下一轮不应继续工具接入或解题，而应修复工程状态闸门暴露出的报告语义问题。

`project_state/task_packet.json` 与 `project_state/current_state.json` 仍保留旧 `samplereverse` sample_state 背景：`task_packet.task=collect_missing_evidence`、`sample=samplereverse`、`current_state.workflow_status=REPORT_AVAILABLE`。这些只能作为历史背景，不能覆盖本 decision。当前轮执行权威是本 `decision_packet.md`。

`project_state/decision_packet.md` 上一轮为 `decision_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`，主线 `tool_integration`，状态 `APPROVED`。该轮已经被 `codex_report_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1` 消耗。

`project_state/codex_execution_report.md` 顶部 `codex_report_summary` 写入：`status=SUCCESS`，`acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`。但 `project_state/gates/report_summary_synthesis.json` 的 `synthesis_status=FAILED`，并给出 synthesized summary：`status=PARTIAL`，`acceptance_recommendation=NEEDS_REVIEW`，差异字段为 `status` 和 `acceptance_recommendation`。

`project_state/gates/final_gate_result.json` 当前 `gate_status=WARN`，`status_summary.report_status=PARTIAL`，`status_summary.report_acceptance_recommendation=NEEDS_REVIEW`；但 `project_state/pytest_result.txt` 中记录的 final-check CLI 输出为 `final-check: PASSED`，这说明 CLI 输出、JSON artifact、报告 summary 三者状态语义未完全统一。

`project_state/pytest_result.txt` 已绑定上一轮 decision/report/round，命令记录完整，测试通过，包括：

- `python -m pytest tests/test_local_reverse_single_sample_static_triage.py tests/test_local_reverse_training_status.py -q`
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- IDA resolver verification
- static triage command
- artifact_index verification
- doctor / lint-report / report-summary / final-check / close-round

`project_state/artifact_index.json` 已包含 `local_reverse_cpp1_2f6fcb63_static_triage`，freshness 为 `current`，source_run 为 `round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1`，tool_status 为 `success`。这不是本轮要重建的对象。

`project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 显示 `executed_sample=false`、`static_only=true`、`runtime_validated=false`、`tool_status=success`、`candidate=null`、`known_candidate=""`。说明上一轮工具接入成功但仍不是 solved 状态；本轮不得把该静态 evidence 升级为 solved。

`negative_results.json` 仍禁止旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration` 为 active，version=2；本 decision 的 `skill_profiles=["reverse-agent-iteration@v2"]` 合法。

已有相关能力：`reverse_agent/project_gate.py`、`reverse_agent/project_state.py`、`tests/test_project_gate.py`、`tests/test_project_state.py`、`project_state/gates/report_summary_synthesis.json`、`project_state/gates/final_gate_result.json`、round closeout 机制。不得新建第二套 gate/report 状态系统。

## 3. Do Not Do

不得运行任何逆向样本二进制；不得运行 IDA、Ghidra、debugger、emulator、hook、harness campaign、solver、bruteforce、SMT 或 runtime probe。

不得继续分析、求解、验证 `cpp1_2f6fcb63`；不得生成 candidate、flag、password；不得修改 `local_reverse_training_status.json` 将样本标记为 solved。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不得重建或覆盖 `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`，除非测试 fixture 需要在临时目录中构造样例。

不得修改 `.codex-skills/`、raw sample 文件、`training_materials/`、solver、strategy、transform、IDA runner 或 local reverse triage adapter。

不得通过手工编辑 gate output 掩盖问题。必须修复生成逻辑和测试，使下一轮真实命令自然产生一致状态。

不得把 `task_packet.task=collect_missing_evidence` 当作当前任务；该字段是旧背景。

不得把 `report-summary` 的 `synthesis_status=FAILED` 降级为无意义 warning，除非规则中明确说明何时允许，并有测试覆盖。

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

- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_baseline.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/round_manifest.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/codex_execution_report.md`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_triage_tooling_rework_v1/pytest_result.txt`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

只允许在需要理解状态语义时有界读取上一轮 live/archived gate artifacts；不得扩大到 solve_reports 或样本分析产物。

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 samplereverse 背景，不能覆盖本 decision。
- 上一轮 `cpp1_2f6fcb63` static triage artifact 已经 current，不是本轮目标。
- `report_summary_synthesis.json` 的 `synthesis_status=FAILED` 与 `codex_report_summary` 的 `SUCCESS/ACCEPTED_WITH_LIMITATIONS` 存在状态口径冲突。
- `final_gate_result.json` 的 `gate_status=WARN` 与 `pytest_result.txt` 中 `final-check: PASSED` 存在 CLI/artifact 输出口径冲突。
- `round_delta_summary.json` 中 inherited dirty files 已被记录；本轮不得把 inherited dirty source/test 文件当成新修改，除非实际修改并在 report 中说明。

必须完成或如实报告：

- 明确 `report-summary` 的合成失败是否应阻断 final-check，或是否应要求 report 顶部 summary 使用 synthesized status。规则必须可测试、可解释。
- 修复 `project_gate final-check` 的 CLI 输出与 `final_gate_result.json.gate_status` 一致性：如果 artifact 为 WARN，CLI 不得显示纯 `PASSED`；可以显示 `WARN` 并 exit 0，或按规则 exit nonzero，但必须有测试。
- 修复或扩展 report-summary/final-check 状态策略，使 `codex_report_summary`、synthesized summary、final gate status、pytest command evidence 的关系稳定。
- 如果 `report_summary_synthesis.json.synthesis_status=FAILED` 仍允许 close-round，必须在 final gate result 中明确 `recommended_next_action` 和 limitation，不得同时给出无条件通过语义。
- 若修改 report status policy，必须更新 tests 覆盖以下场景：
  - report summary 与 synthesized summary 完全一致；
  - report summary 的 status/acceptance_recommendation 与 synthesized summary 不一致；
  - final gate JSON 为 WARN 时 CLI 输出也为 WARN 或等价非纯通过状态；
  - archived report/pytest 与 live report/pytest 一致性不被破坏。
- 本轮 codex_execution_report 必须按实际 gate 结果填写 status。若仍存在 synthesis mismatch，不得写 `SUCCESS/ACCEPTED`。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`，仅限 report/gate/status policy 与 lint/doctor 输出口径必要修复

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py`

Allowed generated/state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_gate_status_semantics_rework_v1/*`

Read-only only:

- `project_state/artifact_index.json`
- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- previous round archives

Forbidden:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw sample files
- `training_materials/`
- IDA/Ghidra/debugger/tool runner code
- local reverse triage adapter
- solver/strategy/transform/runtime/harness modules
- any sample candidate/flag/password artifacts

## 7. Tests

必须真实运行并记录到 `project_state/pytest_result.txt`：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_gate_status_semantics_rework_v1`

如果修复引入新的 CLI 状态文本，测试必须断言 stdout 与生成的 JSON artifact 状态一致。

如果 final-check 对 WARN 选择 exit 0，必须在 stdout 中明确 `final-check: WARN`，并在 JSON 中给出 `recommended_next_action`；不能显示 `PASSED`。

如果 final-check 对 synthesis mismatch 选择 exit nonzero，必须停止 close-round，并在 report 中写 `REWORK_REQUIRED`。

`close-round` 只能在 final-check 符合新状态规则后执行；若 final-check 失败，不得创建 round archive。

## 8. Stop Conditions

如果需要运行 IDA、样本、debugger、emulator、hook、runtime probe、solver、bruteforce 或 harness，立即停止并报告 `BLOCKED`。

如果需要修改 forbidden paths，立即停止并报告 `BLOCKED`。

如果无法复现 `report_summary_synthesis.json` 与 `codex_report_summary` 的 mismatch，先在 report 中说明原因，不得盲改 gate 逻辑。

如果修复后 `report-summary`、`final-check`、`pytest_result`、`codex_execution_report` 仍出现状态口径不一致，必须报告 `REWORK_REQUIRED`，不得写 `SUCCESS/ACCEPTED`。

如果 `pytest_result.txt` 缺失、未覆盖本 decision，或 report/decision/round 不匹配，必须报告 `REWORK_REQUIRED`。

如果发现当前状态文件需要整体重建才能继续，停止源码修改，建议运行：

```bash
python -m reverse_agent.project_state build
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260614_gate_close_round_idempotency_status_policy_rework_v1",
  "round_id": "round_20260614_gate_close_round_idempotency_status_policy_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `project_gate final-check` 与 `project_gate close-round` 的状态机不一致问题，重点处理：

1. standalone `final-check` 在 round 已归档后仍按归档前/全局历史 artifact 策略失败的问题；
2. `close-round` 在 archive 已存在时不可幂等、需要人工删除 archive 才能重跑的问题；
3. `close-round` 成功关闭后，后续 standalone `final-check` 可把 `final_gate_result.json` 覆盖成 FAILED 的问题；
4. `codex_execution_report.md` 自报 `SUCCESS/ACCEPTED_WITH_LIMITATIONS` 与 `final_gate_result.json` 的 `FAILED/REWORK_REQUIRED` 发生冲突的问题；
5. reverse_solving 主线下历史 `samplereverse` missing artifacts 被当成本轮 blocking issue 的问题。

本轮主线是 `engineering_branch`。目标只限 gate / closeout / report-summary / pytest-result / round archive 状态语义和幂等性，不推进 `cpp1_2f6fcb63` 求解，不修改 solver 语义，不运行样本，不改训练队列。

## 2. Current Evidence

当前上一轮 `decision_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1` 的业务产物本身是有价值的：它从 current revalidation artifact 生成了 `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`，并确认 static inverse handoff 为 `status=BLOCKED`、`blocked_reason=NO_COMPLETE_PRINTABLE_PREIMAGE_UNDER_CURRENT_TARGET_BYTES`，没有运行样本、没有 runtime validation、没有标记 solved。

当前 `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json` 已记录：`analysis_mode=static_inverse_transform_handoff`、`mainline=reverse_solving`、`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`authoritative=false`、`requires_runtime_validation=true`、`status=BLOCKED`。该产物可以作为后续线索，但本轮不继续求解。

当前 `project_state/artifact_index.json` 已登记 `local_reverse_cpp1_2f6fcb63_static_inverse_handoff` 为 `freshness=current`，`source_run=round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1`，sample_id 为 `cpp1_2f6fcb63`。

当前 `project_state/negative_results.json` 已新增 `cpp1_2f6fcb63 current target bytes printable inverse path`，原因是 current revalidation 下 printable ASCII inverse 缺失 indices `2, 3, 4, 5, 7, 8, 9, 10, 12, 13`。该 negative result 后续要尊重，本轮不重复该求解方向。

当前 gate/closeout 状态存在冲突：

- `project_state/codex_execution_report.md` 顶部 `codex_report_summary` 仍写 `status=SUCCESS`、`acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`。
- `project_state/gates/final_gate_result.json` 却写 `gate_status=FAILED`，`blocking_reasons` 包含 `status_policy_valid: status policy found blocking issues`，`status_summary.report_status=FAILED`，`status_summary.report_acceptance_recommendation=REWORK_REQUIRED`。
- `pytest_result.txt` 中 `close-round` 输出又显示 archive 已创建、`recommended_next_action=no_action_required`，说明 close-round 路径和 standalone final-check 路径的语义没有收敛。

用户已观察到具体失败模式：standalone `final-check` 在归档后因为 reverse_solving 的历史 missing artifacts 返回失败；`close-round` 已经把这类 status_policy 作为归档后限制处理并成功关闭。随后为了恢复 closeout 结果，需要删除本轮 archive 目录再重跑 `close-round`，并手工同步 live/archive report 和 pytest。这说明当前机制存在结构性问题，而非单纯本轮样本问题。

当前 `task_packet.json` 与 `current_state.json` 仍保留旧 `samplereverse` 背景，不能作为本轮工程 gate 任务的执行权威；当前执行权威是本 `project_state/decision_packet.md`。

`.codex-skills/registry.json` 显示 `reverse-agent-iteration` 是 active，version=2；本 decision 使用的 `reverse-agent-iteration@v2` 合法。

现有相关能力必须复用：`reverse_agent/project_gate.py`、`reverse_agent/project_state.py`、`tests/test_project_gate.py`、`tests/test_project_state.py`、`project_gate report-summary/final-check/close-round`、round archive manifest 机制、pytest_result command block 解析与 command-plan 一致性检查。不得新建第二套 gate runner 或外部 workflow engine。

## 3. Do Not Do

不得推进 `cpp1_2f6fcb63` 求解；不得修改 `local_reverse_cpp1_signed_transform_recheck.py`、`local_reverse_cpp1_target_byte_extract.py` 或任何 solver/transform 逻辑。

不得运行目标样本、IDA、Ghidra、radare2、objdump、debugger、emulator、hook、harness、runtime probe、bruteforce、SMT 或 `sample_solver`。

不得删除已有 round archive 作为正常修复手段。archive 已存在时，`close-round` 必须幂等校验并返回 already_closed/verified_closed 类结果；只有测试临时目录可以模拟删除/重建。

不得在 `close-round` 之后追加 live `pytest_result.txt` command block。live closeout 命令记录仍必须以 `close-round` 为最后 command block。

不得手工伪造 stdout/stderr、final_gate_result、report-summary 或 archive manifest。所有状态文件必须由命令真实生成。

不得把历史 `samplereverse` missing artifacts 当成本轮 gate 的 blocking issue，除非当前 decision 明确依赖这些 artifacts。

不得修改 raw sample、`training_materials/`、`.codex-skills/`、完整 `solve_reports/`、训练状态/队列语义、candidate/flag/password artifact。

不得把 `task_packet.task` 或旧 sample_state 覆盖当前 decision。

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

- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/round_manifest.json`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/codex_execution_report.md`
- `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/pytest_result.txt`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

只读核验：

- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，skill profile 来自 active registry。
- 当前任务是工程 gate 修复，不是 reverse_solving 继续推进。
- 上一轮 static inverse handoff 的业务 artifact 可以保留为线索，但本轮不修改它。
- 当前失败的核心是 final-check/close-round/report-summary/status-policy 状态不一致，而不是样本求解失败。

必须完成的审计与修复：

1. 梳理 `project_gate final-check` 与 `project_gate close-round` 共用和分叉的检查路径，找出为什么 close-round 能关闭而 standalone final-check 仍写 `gate_status=FAILED`。
2. 为 final-check 引入明确的阶段语义，至少区分：
   - pre-close：archive 尚未创建或即将 close-round；
   - post-close：round manifest 已存在，应校验 live/archive 一致性，而不是重新套用归档前缺失策略；
   - stale-after-close：如果 live report/pytest 与 archive 不一致，必须 FAIL，并提示不要覆盖 archive。
3. 修复 `close-round` 幂等性：
   - archive 不存在时，执行正常 close；
   - archive 已存在且 live/archive 一致时，返回 exit 0，状态为 already_closed/verified_closed，不删除 archive、不重写 archive；
   - archive 已存在但 live/archive 不一致时，返回 BLOCKED/FAILED，除非显式提供未来设计的 rearchive 选项；本轮不要求实现 force rearchive。
4. 修复 status_policy：reverse_solving 下历史 missing artifacts 只有在当前 decision scope 或 current artifact dependency 中被要求时才 blocking；旧 `samplereverse` missing artifacts、旧 global sample artifacts 应降级为 WARN 或 limitations。
5. 修复 report status 派生/校验：
   - 若 final_gate_result 是 FAILED，report 不得写 SUCCESS；
   - 若 close-round 成功且把历史 missing artifact 降为 limitation，final_gate_result/report-summary/report status 必须一致；
   - `report_summary_synthesis.json` 必须能准确反映 final gate 的 source，不允许 report 自报和 gate 冲突。
6. 修复 live `pytest_result.txt` 与 archive 更新流程：
   - 不能靠手工写回 close-round block；
   - close-round 后不追加命令；
   - archived report/pytest 必须与 live 一致；
   - standalone post-close final-check 不应破坏已关闭 round 的 closeout 证据。
7. 修复或新增测试覆盖 close-round archive already exists 的幂等行为，以及 post-close final-check 不会把历史 unrelated missing artifacts 升级为 FAIL。

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`，仅限 doctor/lint/report status policy 或 archive status 兼容修复

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
- `project_state/rounds/round_20260614_gate_close_round_idempotency_status_policy_rework_v1/*`

Read-only only:

- previous round archive `project_state/rounds/round_20260614_cpp1_2f6fcb63_static_inverse_handoff_v1/*`
- `project_state/local_reverse_cpp1_2f6fcb63_static_inverse_handoff.json`
- `project_state/local_reverse_cpp1_2f6fcb63_target_bytes_revalidation.json`
- `project_state/artifact_index.json` unless a generated gate/status cache update requires reading it; do not change sample artifact entries in this round
- `project_state/negative_results.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`

Forbidden:

- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample files
- solver/harness/runtime/debugger/emulator code
- `reverse_agent/local_reverse_cpp1_signed_transform_recheck.py`
- `reverse_agent/local_reverse_cpp1_target_byte_extract.py`
- `reverse_agent/strategies/`
- `reverse_agent/transforms/`
- any candidate/flag/password artifact
- any state change marking `cpp1_2f6fcb63` solved

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
- close-round idempotency unit test evidence：通过 pytest 覆盖 archive exists + live/archive match 返回 verified/already closed，不删除 archive
- post-close final-check unit test evidence：通过 pytest 覆盖 archived round 中 standalone final-check 不因 unrelated historical missing artifacts 失败
- status policy unit test evidence：通过 pytest 覆盖 current decision required artifact missing 才 FAIL，unrelated historical missing artifact 只 WARN
- report/gate mismatch unit test evidence：通过 pytest 覆盖 final_gate FAILED 时 report SUCCESS 不可通过 synthesis/final-check
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260614_gate_close_round_idempotency_status_policy_rework_v1`

可选但推荐在 pytest 单元测试中完成，不要求作为 live close-round 后 command block：

- 模拟 archive 已存在时第二次 close-round 返回 already_closed/verified_closed；
- 模拟 post-close final-check 不覆盖已关闭 round 的成功 closeout；
- 模拟 live/archive diverged 时返回 FAILED/BLOCKED。

`close-round` 必须是 live `pytest_result.txt` 与 archived pytest 中最后一个 command block。不得为了验证 post-close 行为而在 live pytest 中 close-round 后追加 command block；post-close 行为应由 pytest 临时目录测试覆盖。

## 8. Stop Conditions

如果修复需要删除已有真实 round archive 才能通过，停止并报告 `REWORK_REQUIRED`。本轮目标是幂等 close-round，不是删除重建 archive。

如果 standalone final-check 和 close-round 仍能产生互相矛盾的 final_gate/report_summary 状态，停止并报告 `REWORK_REQUIRED`。

如果历史 unrelated missing artifacts 仍导致当前 engineering_branch gate 失败，停止并报告 `REWORK_REQUIRED`。

如果 final_gate_result 是 FAILED 但 report 仍写 SUCCESS/ACCEPTED，停止并报告 `REWORK_REQUIRED`。

如果需要修改 solver/sample/training files 或触碰 raw samples，停止并报告 `BLOCKED`。

如果测试或 gate 失败，`codex_execution_report.md` 必须写 `FAILED/REWORK_REQUIRED` 或 `BLOCKED`，不能写 `SUCCESS/ACCEPTED`。

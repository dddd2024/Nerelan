```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_tool_integration_artifact_policy_closeout_v1",
  "round_id": "round_20260613_tool_integration_artifact_policy_closeout_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

返工 `decision_20260613_affineenc_static_triage_v1` 的工程 closeout：修复或显式收敛 gate 在 `tool_integration` 主线下把 historical missing artifacts 视为 blocking 的策略问题，使已经完成的 `affineenc_333f8ca9` 静态 triage round 能形成 report-summary / final-check / close-round / archive 一致闭环。

本轮不是重新训练、不是继续分析 `affineenc_333f8ca9`，也不是样本求解。上一轮 `affineenc_333f8ca9` 静态 triage 核心产物已经成功生成并登记；本轮只处理 gate/status policy/报告归档闭环，确保不把历史 `samplereverse` missing artifacts 错误作为当前 tool_integration round 的阻塞项。

## 2. Current Evidence

当前主线为 `engineering_branch`，因为本轮目标是 gate/status policy 和 round closeout 的工程修复，不是 reverse_solving、tool_integration 内容推进或 training_dataset 批量处理。

`project_state/decision_packet.md` 是当前轮执行权威。`project_state/task_packet.json` 和 `project_state/current_state.json` 仍是旧 `samplereverse` sample_state，只能作为背景，不能覆盖本 decision。不得根据 `task_packet.task=collect_missing_evidence` 回到旧 `samplereverse` 求解线。

上一轮 `decision_20260613_affineenc_static_triage_v1` 的样本静态 triage 已完成：`project_state/local_reverse_affineenc_333f8ca9_static_triage.json` 存在，`tool_status=success`，`source_tool=IDA`，`static_only=true`，`runtime_validated=false`，记录 50 strings、30 functions、2 compare contexts、3 hypotheses。该产物应保留为 current evidence，不得重跑或改写语义。

上一轮 artifact 登记已完成：`artifact_index.json` 中 `local_reverse_affineenc_333f8ca9_static_triage` freshness 为 current，source_run 为 `round_20260613_affineenc_static_triage_v1`。本轮不得把 `affine_8cfebe03` artifact 当作 `affineenc_333f8ca9` 的证据。

上一轮 training/evaluation 状态已完成：`local_reverse_training_status.json` 中 `affineenc_333f8ca9` 已从 `inventory_only` 更新为 `needs_triage`，classification 为 `string_compare_password_checker; standard_input_based; strcmp_direct_compare`，known_candidate 为空，未 solved；`local_reverse_evaluation_queue.json` 中该条目记录 `static_triage_completed=true` 和 `static_triage_run=round_20260613_affineenc_static_triage_v1`。

上一轮未完成项不是样本证据问题，而是 gate closeout 问题：`report-summary` FAILED，`final-check` FAILED，`close-round` FAILED，round manifest 未生成。主要阻塞为 `status_policy_valid` 把 50 个 historical missing artifacts 作为 blocking；这些 missing artifacts 是旧 `samplereverse` 历史状态，不是 `affineenc_333f8ca9` 当前 round 的缺失产物。

上一轮 `codex_execution_report.md` 已如实标记 `status=FAILED`、`acceptance_recommendation=REWORK_REQUIRED`，没有错误宣称 complete。上一轮 `pytest_result.txt` 中 302 个 project gate/state 测试通过，static triage 命令 exit code 为 0，但 close-round 未归档。

`negative_results.json` 中禁止回到旧 sample_solver 盲搜、只扩大 beam/budget、使用 compare_semantics_agree=false 作为主 frontier、提交完整 solve_reports、重复旧 samplereverse 失败方向。本轮不触碰这些方向。

已有相关能力必须优先复用：project_gate final-check/status_policy_valid/close-round/report-summary、project_state doctor/lint-report、round archive、artifact_index、training_status、evaluation_queue。不得新建重复 gate 系统或重复 IDA/Ghidra/debugger/solver/harness 接口。

涉及逆向工具边界：本轮不运行 IDA/Ghidra/static triage，不运行 solver、runtime probe、debugger、emulator、hook、harness campaign，不生成 candidate。只允许读取上一轮 current artifact 来核验证据未被破坏。

允许读取重型 artifact：不允许读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。只允许读取本轮直接相关的 project_state 文件、上一轮 `affineenc` 静态 triage artifact、gate/round 文件、project_gate/project_state 最小源码和相关测试。

## 3. Do Not Do

不得重跑 `affineenc_333f8ca9` static triage、IDA static extraction、forced IDA、xref extraction，除非只是检查文件存在性和读取当前 artifact 内容。

不得重复 `affine_8cfebe03` 的 static evidence classification、static tool blocker/state closure、audit closure 或任何旧训练任务。

不得运行 solver、bruteforce、guided_pool、sample_solver、SMT、runtime validation、debugger、emulator、hook、harness campaign。

不得生成 candidate、flag、password；不得把 `affineenc_333f8ca9` 标成 solved。

不得修改 `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` 的语义字段；不得修改 `affineenc_333f8ca9` 的 known_candidate 或 solved 状态。

不得处理 evaluation queue rank 2 及以后样本，不得批量跑 inventory_only 样本。

不得读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，不得提交完整 solve_reports，不得修改 `.codex-skills/`、training materials、raw sample 文件。

不得简单把所有 tool_integration artifact freshness 问题全局放宽。必须保持 reverse_solving 对 stale/missing current evidence 的严格性；只允许将明确属于历史样本、未被当前 report 声称为 current evidence、且不属于当前 round required/generated artifact 的 missing/stale 条目降级为 non-blocking limitation。

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

- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

## 5. Required Audit

Codex 必须先确认：

- 当前 decision_meta 合法，`status=APPROVED`，`mainline=engineering_branch`，`skill_profiles` 来自 active registry。
- `task_packet.json/current_state.json` 是旧 `samplereverse` 背景，当前执行权威是本 decision。
- `affineenc_333f8ca9` static triage artifact 已存在且 tool_status=success、static_only=true、runtime_validated=false。
- `artifact_index.json` 中 `local_reverse_affineenc_333f8ca9_static_triage` 是 current 且 source_run 指向 `round_20260613_affineenc_static_triage_v1`。
- `local_reverse_training_status.json` 中 `affineenc_333f8ca9` 仍为 `needs_triage`，known_candidate 为空，未 solved。
- 上一轮 closeout 失败根因是 gate/status policy 对 historical missing artifacts 的处理，不是 static triage 失败。

必须定位并最小修复：

- `status_policy_valid` 对 artifact_index 中 historical missing/stale artifacts 的处理边界：工程/工具接入 closeout 中，如果当前 round 的 required/generated artifact 都存在且当前 report 没有声称旧 missing artifacts 是 current evidence，应降级为 WARN/PASSED_WITH_LIMITATIONS，而不是 blocking FAIL。
- 保持 reverse_solving 主线严格性：reverse_solving 如果依赖 stale/missing artifact 或把 stale/missing 当 current evidence，仍必须 FAIL。
- 若 `tool_integration` round 是为了生成当前工具证据，且当前工具证据存在并登记为 current，历史 `samplereverse` missing artifacts 不应阻塞 close-round/archive。
- report-summary、final-check、close-round 的最终状态必须与 codex_report_summary 一致；不得让 synthesis 期待 FAILED 而 report 写 SUCCESS。
- close-round 必须生成 `project_state/rounds/round_20260613_tool_integration_artifact_policy_closeout_v1/round_manifest.json`，并归档本轮 decision/report/pytest。

还必须确认不破坏上一轮样本成果：

- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` 内容不被语义改写。
- `affineenc_333f8ca9` training_status 不变成 solved，known_candidate 仍为空。
- `affine_8cfebe03`、`cpp1_bcbd9979`、`cpp2_4c69f173`、`sha_256_18019fca` 的既有训练结论不被修改。

## 6. Implementation Scope

Allowed

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260613_tool_integration_artifact_policy_closeout_v1/*`

Allowed only for metadata consistency if required by final gate, without changing sample evidence semantics:

- `project_state/artifact_index.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`

Forbidden

- `project_state/local_reverse_affineenc_333f8ca9_static_triage.json` semantic fields
- `project_state/local_reverse_affine_8cfebe03_static_evidence_summary.json` semantic fields
- solver、harness、debugger、emulator、runtime probe、candidate validation 相关代码
- `reverse_agent/strategies/`、`reverse_agent/transforms/`、IDA/Ghidra/debugger 新接口
- `.codex-skills/`
- `training_materials/`
- `solve_reports/`
- raw sample 文件
- queue rank 2 及以后样本状态

## 7. Tests

必须运行并记录：

- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- targeted pytest covering the status_policy_valid / historical artifacts downgrade behavior for engineering_branch, training_dataset, tool_integration, and preserving reverse_solving strictness
- `python -m pytest tests/test_project_state.py tests/test_project_gate.py -q`
- artifact/training status核验：`affineenc_333f8ca9` artifact exists/current；training_status remains needs_triage；known_candidate empty；not solved
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260613_tool_integration_artifact_policy_closeout_v1`
- close-round 后重新运行或记录最终 `report-summary` / `final-check` 状态，确保 archive 后状态一致

`project_state/pytest_result.txt` 必须包含本轮 `decision_20260613_tool_integration_artifact_policy_closeout_v1`、`round_20260613_tool_integration_artifact_policy_closeout_v1`、真实命令、退出码和最终结果。

`project_state/codex_execution_report.md` 顶部必须包含合法 `codex_report_summary`，其中 `based_on_decision_id=decision_20260613_tool_integration_artifact_policy_closeout_v1`，`round_id=round_20260613_tool_integration_artifact_policy_closeout_v1`，并列出实际 files_changed、tests_ran、generated_artifacts。

## 8. Stop Conditions

如果需要重跑 IDA/static triage、solver、runtime validation、debugger、emulator、hook、harness campaign，停止并报告 BLOCKED。

如果需要修改 `.codex-skills/`、training materials、solve_reports 历史目录或 raw sample 文件，停止。

如果需要把 `affineenc_333f8ca9` 标成 solved、写入 candidate、或继续做约束恢复/运行时验证，停止。

如果无法在不削弱 reverse_solving 严格性的前提下让 historical missing artifacts 在 tool_integration closeout 中降级为 non-blocking limitation，停止并报告 REWORK_REQUIRED，给出更小的 policy 设计方案。

如果 report-summary/final-check/close-round/archive 仍存在 FAIL，`codex_execution_report.md` 必须标记 FAILED/REWORK_REQUIRED 或 BLOCKED，不能写 SUCCESS/ACCEPTED。

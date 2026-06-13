```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260613_gate_status_policy_for_static_tool_success_v1",
  "round_id": "round_20260613_gate_status_policy_for_static_tool_success_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 gate/report 状态策略循环问题。当前事实是上一轮 tool_integration 已成功验证 `affine_8cfebe03` 的 IDA static extraction，且已生成 success static triage artifact 和 diagnostic artifact；但 live final-check 仍因历史 sample artifact 缺失和 synthesis 回读循环被判为 FAILED。本轮只修 gate/status policy、report-summary synthesis、artifact_index 和 closeout 一致性，不继续解题。

## 2. Current Evidence

当前 `decision_packet.md` 是执行权威，旧 `task_packet.json/current_state.json` 仍是 `samplereverse` 历史 sample_state，只能作背景。上一轮 `decision_20260613_static_tool_validation_state_closure_v1` 已将 report status 改为 SUCCESS、pytest_result header 改为 PASSED，并记录 gate/state pytest 342 passed。但 live `final_gate_result.json` 仍为 FAILED，blocking reason 是 `status_policy_valid` 将 `50 missing, 0 stale artifacts` 作为 blocking lint error；`report_summary_synthesis.json` 继续合成 FAILED/REWORK_REQUIRED，与 report SUCCESS/ACCEPTED 冲突。`artifact_index.json` 仍指向旧 1064-byte blocker artifact，而不是本轮 success static triage artifact。

## 3. Do Not Do

不修改 IDA 输出目录逻辑。不运行 solver。不生成 candidate、flag、password。不运行 runtime validation、debugger、emulator、hook 或 harness campaign。不处理新样本。不修改 `.codex-skills/`、training materials、solve_reports 或 raw sample 文件。不把 50 个历史 sample artifact 缺失当作当前 tool_integration 失败。不通过删除检查、跳过 gate 或硬写假 PASS 制造通过结果。

## 4. Files To Inspect

必须读取 project_state 默认文件、上一轮 decision/report/pytest_result、`project_state/gates/final_gate_result.json`、`project_state/gates/report_summary_synthesis.json`、`project_state/gates/round_delta_summary.json`、`project_state/artifact_index.json`、`project_state/local_reverse_affine_8cfebe03_static_triage.json`、`project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`、`project_state/rounds/round_20260613_static_tool_validation_state_closure_v1/round_manifest.json`，以及 `reverse_agent/project_gate.py`、`reverse_agent/project_state.py` 和对应 gate/state 测试。

## 5. Required Audit

Codex 必须确认：当前 decision 合法且 skill active；IDA static extraction success artifact 与 diagnostic artifact 是当前验证证据；50 missing artifacts 属于历史 sample artifact 限制，不是本轮 tool_integration blocker；artifact_index 是否仍指向旧 artifact；report-summary 是否从 live final_gate_result 反向合成失败状态造成循环；close-round/archive 是否在 archive 后再次运行 final-check 并把旧状态写回；若需要改 gate 策略，必须用测试证明不会掩盖真实 missing/stale current artifacts。

## 6. Implementation Scope

允许最小修改 `reverse_agent/project_gate.py`、`reverse_agent/project_state.py`、`tests/test_project_gate.py`、`tests/test_project_state.py`。允许更新 `project_state/artifact_index.json`、`project_state/codex_execution_report.md`、`project_state/pytest_result.txt`、`project_state/gates/*.json`、`project_state/rounds/round_20260613_gate_status_policy_for_static_tool_success_v1/*`。

必须更新 `artifact_index.json`，使 `local_reverse_affine_8cfebe03_static_triage` 指向当前 success artifact，而不是旧 blocker artifact。必须保留 `project_state/static_tool_blocker_diagnostic_affine_8cfebe03.json`，不得删除。

不得修改 `reverse_agent/local_reverse_single_sample_static_triage.py`、`reverse_agent/local_reverse_forced_ida_extract.py`、`reverse_agent/local_reverse_xref_disassembly.py`、solver、harness campaign、debugger scripts、skill、training materials、solve_reports 历史目录或 raw sample 文件。

## 7. Tests

必须记录：位置确认、git 状态、preflight、command-plan、command-plan json、`python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`、doctor、lint-report、report-summary、final-check、close-round/archive、diff 文件名。若修改 artifact_index policy，必须增加或更新测试覆盖：历史 missing sample artifacts 在非 sample-solving closeout 中只能降级为 limitation/WARN；current artifact missing/stale 仍应保持阻塞。

验收要求：final-check 不得为 FAILED；report-summary 无 ERROR 且无 status diff；artifact_index 指向本轮 success artifact；codex_report_summary 与 synthesis 一致；round archive 存在；不得新增测试失败。

## 8. Stop Conditions

若需要重新运行 IDA smoke，可只作为静态验证，不得运行样本或 runtime probe。若需要 runtime/debugger/solver/harness 或新样本分析，停止。若需要修改 skill、training materials、solve_reports 或 raw sample 文件，停止。若无法安全区分历史 missing artifacts 与当前 missing/stale artifacts，停止并报告 BLOCKED。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework_tool_inventory_closeout_consistency_v1",
  "round_id": "round_20260612_rework_tool_inventory_closeout_consistency_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

只返工上一轮 `tool_integration` closeout 一致性，不扩展工具库存内容，不进入样本 triage，不新增求解能力。

目标是让以下六类状态完全一致并通过 final-check：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_rework_tool_inventory_closeout_consistency_v1/*`

上一轮已经生成 `project_state/tool_capability_inventory.json` 与 `project_state/structured_evidence_gap_report.json`，本轮只允许校正 closeout、report、gate、round archive 一致性；不得继续扩展 inventory/gap report 的内容范围。

## 2. Current Evidence

- 当前上一轮 report 是 `codex_report_20260612_tool_integration_capability_inventory_v1`，`status=PARTIAL`，`acceptance_recommendation=CONDITIONAL`，不能作为已验收完成状态。
- 当前 `project_state/gates/final_gate_result.json` 的 `gate_status=FAILED`。
- 当前 `project_state/gates/report_summary_synthesis.json` 的 `synthesis_status=FAILED`。
- 当前 `pytest_result.txt` 记录 `lint-report`、`doctor`、`doctor --json`、`report-summary`、`final-check`、`final-check --json` 曾以 exit code 1 失败，虽然后续 `close-round` 后又记录 final-check PASSED，但 live `final_gate_result.json` 仍是 FAILED，说明收尾产物不一致。
- 当前 final gate blocking reasons 包括：
  - `files_changed_covers_git_diff` 失败。
  - `baseline_lifecycle_guard` 失败。
  - `generated_artifacts_cover_round_archive` 失败。
  - `pytest_result_exit_codes_match_command_plan` 失败。
  - `command_plan_json_stdout_full` 失败。
  - `report_summary_fields_match_synthesis` 失败。
  - `status_policy_valid` 失败。
- 当前 baseline 包含历史 dirty files，其中有 `reverse_agent/project_state.py` 和 `tests/test_project_state.py`；上一轮没有显式 inherited allowlist，因此 baseline lifecycle guard 触发失败。
- 当前 `files_changed` / `generated_artifacts` 使用了 wildcard archive path：`project_state/rounds/round_20260612_tool_integration_capability_inventory_v1/*`。这不满足 report-summary 自动合成的精确路径要求。
- 当前 `project_state/tool_capability_inventory.json` 和 `project_state/structured_evidence_gap_report.json` 可作为已生成产物保留，但本轮不得把其内容继续扩大或用于样本求解。
- `task_packet.json` 仍只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `current_state.json` 和 `artifact_index.json` 仍包含旧 sample-solving 事实与 stale/missing artifact；本轮不得把这些 stale artifact 当作 current evidence。
- `negative_results.json` 禁止旧 sample_solver blind search、扩 beam/budget、compare_semantics_agree=false candidate、提交完整 solve_reports 等方向。本轮不得触碰这些方向。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver 或 candidate search。
- 不运行 radare2、objdump、strings、file 等外部静态工具处理样本。
- 不生成 candidate、flag、password 或答案。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取、上传或复制 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不修改训练队列业务分类规则。
- 不继续扩展 `tool_capability_inventory.json` / `structured_evidence_gap_report.json` 的能力内容；只可重生成以对齐 decision/round/report schema。
- 不把 wildcard round archive 路径继续写进 `files_changed` 或 `generated_artifacts`。
- 不把失败命令记录保留为本轮最终 tests_ran 的通过证据。
- 不通过降低 final-check / report-summary 校验强度来制造假通过。

## 4. Files To Inspect

必须读取：

- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/tool_capability_inventory.json`
- `project_state/structured_evidence_gap_report.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/tool_capability_inventory.py`
- `tests/test_tool_capability_inventory.py`

可有界读取：

- `tests/test_project_gate.py`，仅用于 closeout/report-summary/final-check 相关测试失败定位。
- `tests/test_project_state.py`，仅用于 lint/doctor 相关测试失败定位。
- 最新上一轮 commit diff 或 round artifact manifest，若需要确认为什么 live artifacts 与 report 不一致。

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须解释并修复：

1. 为什么上一轮 report 是 `PARTIAL/CONDITIONAL`，不能作为成功验收。
2. 为什么当前 live `final_gate_result.json` 仍为 FAILED，而 `pytest_result.txt` 后半段又记录 final-check PASSED。
3. 为什么 `report_summary_synthesis.json` 是 FAILED。
4. 为什么 `command-plan --json` stdout 没有记录完整 JSON commands array。
5. 为什么 `lint-report`、`doctor`、`doctor --json`、`report-summary`、`final-check`、`final-check --json` 曾记录 exit code 1。
6. 为什么 `files_changed` / `generated_artifacts` 使用 wildcard archive 路径，以及如何改为精确 round archive 文件路径。
7. 为什么 baseline 仍包含未授权 source/test inherited dirty files，并决定本轮应如何处理：
   - 若这些文件确为进入本轮前历史 baseline，必须在本轮 decision/report 中显式说明并列入 allowed inherited baseline；或
   - 若这些文件实际是本轮应修改文件，必须重新生成 clean baseline 或把它们纳入本轮真实 `files_changed`，不得静默忽略。
8. 确认 `tool_capability_inventory.json` 与 `structured_evidence_gap_report.json` 仍存在，且 decision_id/round_id 可以对齐本轮 rework 或明确作为上一轮产物被本轮验证。
9. 确认本轮没有运行样本、IDA/Ghidra/debugger/radare2/file/strings/objdump、harness campaign、solver、candidate search 或 runtime probe。

## 5b. Allowed Inherited Dirty Baseline Files

以下文件为进入本轮前已存在的 baseline dirty files，本轮不修改它们（或仅做 decision 授权的最小修改）：

- `reverse_agent/harness.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/artifact_index.json`
- `project_state/decision_packet.md`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`

## 6. Implementation Scope

允许修改：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/preflight_result.json`
- `project_state/tool_capability_inventory.json` only to update decision_id/round_id/provenance if required by closeout consistency
- `project_state/structured_evidence_gap_report.json` only to update decision_id/round_id/provenance if required by closeout consistency
- `project_state/rounds/round_20260612_rework_tool_inventory_closeout_consistency_v1/*`
- `reverse_agent/project_gate.py` only if needed to fix command-plan/report-summary/final-check closeout consistency without weakening checks
- `tests/test_project_gate.py` only if needed for closeout regression coverage
- `tests/test_tool_capability_inventory.py` only if needed to keep inventory CLI tests green after provenance-only updates

不允许修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/queue.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_training_next_queue.json`
- `project_state/local_reverse_training_capability_review.json`
- raw local samples
- sample binaries
- solver/harness/IDA/Ghidra/debugger execution logic
- inventory/gap report semantic scope beyond provenance/closeout consistency
- unrelated source modules
- unrelated tests

## 7. Tests

必须重新运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.tool_capability_inventory build --state-dir project_state
python -m pytest tests/test_tool_capability_inventory.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework_tool_inventory_closeout_consistency_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- `python -m pytest tests/test_tool_capability_inventory.py -q` 必须通过。
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q` 必须通过。
- `command-plan` 不得出现 unknown kind。
- `command-plan --json` 的 stdout 必须记录完整 JSON commands array。
- `lint-report`、`doctor`、`doctor --json`、`report-summary`、`final-check`、`final-check --json`、`close-round` 均不得以 exit code 1 作为最终状态。
- `report_summary_synthesis.json` 必须为 `PASSED`。
- `final_gate_result.json` 必须为 `PASSED`。
- `codex_execution_report.md` 的 `codex_report_summary.status` 应为 `SUCCESS`，`acceptance_recommendation` 应为 `ACCEPTED`；若仍为 PARTIAL/CONDITIONAL，必须停止并报告 BLOCKED。
- `files_changed` 和 `generated_artifacts` 必须使用精确路径，不能使用 `round_id/*` wildcard。
- round archive 必须存在，且 archive/live report、pytest_result 一致。
- `tool_capability_inventory.json` 与 `structured_evidence_gap_report.json` 必须存在，且 provenance 对齐本轮 rework 或被 report 明确标记为上一轮产物经本轮验证。
- `pytest_result.txt` 必须包含 fenced `pytest_result_summary` JSON，并覆盖 report 中所有 `tests_ran`。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 无法让 `report_summary_synthesis.json` 和 `final_gate_result.json` 同时 PASSED。
- 无法解释或清理 `PARTIAL/CONDITIONAL` report 状态。
- 无法消除 wildcard archive 路径。
- 无法处理未授权 inherited source/test dirty baseline。
- 需要运行样本、solver、IDA/Ghidra/debugger/radare2/file/strings/objdump 才能完成本轮。
- 需要读取完整 `solve_reports/`。
- 需要修改 `.codex-skills/`。
- final-check 只能通过降低校验强度来通过。

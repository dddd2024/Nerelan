```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_training_metadata_contract_repair_rework_v1",
  "round_id": "round_20260612_training_metadata_contract_repair_rework_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 `training_metadata_contract_repair` 的收尾状态问题。目标不是继续扩展训练集，也不是推进样本求解，而是让 project_state、报告、pytest_result、gate 输出和 git 状态重新一致。

必须保留 `project_state/local_reverse_training_inventory_audit.md` 中已完成的 metadata contract 修补内容，但必须修正以下问题：

1. `pytest_result.txt` summary 不得在实际命令失败时写 `PASSED`。
2. `codex_execution_report.md` 的 `files_changed` 必须覆盖真实 git 变更，或者清理不属于本轮范围的变更。
3. 不得保留 `reverse_agent/harness.py`、`reverse_agent/project_state.py`、`tests/test_project_state.py` 等源码/测试文件的未授权修改。
4. `project_state/gates/final_gate_result.json` 必须最终为 `PASSED`，否则报告不得写 `SUCCESS` / `ACCEPTED`。
5. 若需要修改源码或测试才能通过 gate，必须停止并报告 `BLOCKED`，不得扩大范围。

## 2. Current Evidence

- 上一轮文档修补内容基本正确，`failure_reason`、`solver_used`、`tool_evidence_used` 已进入 audit 文档。
- 上一轮 `final_gate_result.json` 明确为 `FAILED`。
- 上一轮 `pytest_result.txt` summary 写 `PASSED`，但实际记录包含 `lint-report`、`doctor`、`final-check` 失败。
- 上一轮最终 `git status --short` 显示源码/测试文件仍被修改。
- 本轮主线设为 `engineering_branch`，只修复状态一致性和门禁收尾，不推进训练样本、不运行 IDA/Ghidra/debugger、不运行 solver。

## 3. Do Not Do

- 不运行样本。
- 不运行 IDA/Ghidra/debugger/runtime probe。
- 不执行 static triage。
- 不改 `.codex-skills/`。
- 不读取完整 `solve_reports/`。
- 不改 solver、harness、project_state 源码或测试，除非先停止并报告 BLOCKED。
- 不用手工改 summary 掩盖失败命令。
- 不在 final-check 失败时写 `SUCCESS` 或 `ACCEPTED`。

## 4. Files To Inspect

必须读取：

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/local_reverse_training_inventory_audit.md`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/round_manifest.json`
- `.codex-skills/registry.json`

必须用 `git status --short` 和必要的 `git diff --name-only` 核对实际变更。

## 5. Required Audit

Codex 必须：

1. 确认工作目录为 `F:\reverse-agent`。
2. 运行 `git status --short`。
3. 对比上一轮 `final_gate_result.json` 的失败项。
4. 清理或还原未授权的源码/测试改动：`reverse_agent/harness.py`、`reverse_agent/project_state.py`、`tests/test_project_state.py`。
5. 保留 `project_state/local_reverse_training_inventory_audit.md` 中 metadata contract 的有效修补。
6. 重新生成 `codex_execution_report.md`，确保 `files_changed` 覆盖真实变更。
7. 重新记录 `pytest_result.txt`，真实记录每条命令 stdout/stderr/exit code。
8. 重新运行 final-check，必须通过。
9. 重新 archive 本轮 rework round。
10. 如果 final-check 仍失败，则报告 `FAILED` 或 `BLOCKED`，不得写 `SUCCESS`。

## 6. Implementation Scope

允许修改：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_training_metadata_contract_repair_rework_v1/*`

允许保留但不得扩大：

- `project_state/local_reverse_training_inventory_audit.md`

必须还原或移出本轮范围：

- `reverse_agent/harness.py`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

## 7. Tests

必须运行并记录：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_local_reverse_training_status.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_training_metadata_contract_repair_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 无法还原未授权源码/测试改动。
- final-check 失败。
- pytest_result 需要伪造 `PASSED` 才能通过。
- report/decision/round_id 不匹配。
- `files_changed` 无法覆盖真实 git 变更。
- 需要修改源码、测试、schema 或工具接口才能完成收尾。

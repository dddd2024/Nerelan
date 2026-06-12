```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260612_rework4_final_gate_closeout_contract_v1",
  "round_id": "round_20260612_rework4_final_gate_closeout_contract_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

本轮只修复最终 gate closeout 结构问题，不再扩大训练队列功能。

目标：让 `command_plan.json`、`pytest_result.txt`、`codex_execution_report.md`、`final_gate_result.json`、round archive 五者形成一致闭环。只有 `lint-report`、`doctor`、`final-check`、`close-round` 全部通过，才允许写 `SUCCESS + ACCEPTED`。

本轮不是逆向解题。不得运行样本、IDA/Ghidra/debugger/harness/solver，不得生成 candidate、flag、password 或答案。

## 2. Current Evidence

- 当前上一轮功能侧基本完成：queue build 生成 50 样本分桶队列，primary/secondary/reference/blocked 数量符合预期。
- 当前阻塞点是 gate 结构失败，不是训练队列业务逻辑失败。
- `project_state/gates/final_gate_result.json` 当前为 `FAILED`。
- round manifest 缺失。
- archived report/pytest 与 live report/pytest 不一致。
- generated_artifacts 漏 round archive。
- command_plan 仍有 unknown kind。
- pytest_result 缺 command_plan 期望的完整命令块。
- command-plan `--json` stdout 未完整记录。
- report 为 `PARTIAL + NEEDS_REVIEW`。
- `task_packet.json` 只能作为 advisory；当前执行权威是本 `decision_packet.md`。
- `negative_results.json` 禁止旧盲搜、预算扩张、重复 runtime/breakpoint probe、完整 `solve_reports/` 提交等方向。本轮不得触碰这些方向。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 IDA、Ghidra、OllyDbg、x64dbg、debugger、emulator、runtime probe、winpty、harness campaign、solver 或 candidate search。
- 不生成 candidate、flag、password 或答案。
- 不读取完整 `solve_reports/`。
- 不读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不读取或上传 raw sample、sample binary、IDA database、debug trace、大体积历史 artifact。
- 不修改 `.codex-skills/`。
- 不修改训练队列业务规则，除非 final gate 明确要求格式修复。
- 不修改 `reverse_agent/harness.py`，除非上一轮已经改动需要回退。
- 不把 `pytest_result final_conclusion: PASS` 当作最终验收依据；以 final-check、doctor、lint-report、close-round 为准。
- 不通过降低 gate 校验强度来制造假通过。

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260612_rework3_enforce_cleanup_and_queue_contract_v1/` 是否存在
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

只在解释越界变更时有界检查：

- `reverse_agent/harness.py`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`

不得默认读取：完整 `solve_reports/`、完整 `PROJECT_PROGRESS_LOG.txt`、raw local samples、历史大体积 archive。

## 5. Required Audit

Codex 必须回答：

1. 为什么 `command_plan` 中 `git ls-files ...` 和 `local_reverse_training_review build ...` 被标成 `unknown kind`。
2. 是修复 kind classifier，还是调整 final-check 对这两类命令的匹配规则。
3. 为什么 `pytest_result` 里明明记录了部分命令，但 final-check 认为 recorded command block 缺失。
4. 是否因为命令字符串缩写、`python -m pytest` vs `pytest`、省略号 `...`、或 block parser 格式导致匹配失败。
5. 为什么 `close-round` 后没有有效 round manifest。
6. archived report/pytest 为什么与 live report/pytest 不一致。
7. report 的 `generated_artifacts` 是否必须包含 round manifest。
8. 上一轮 `files_changed` 中的 `reverse_agent/harness.py`、`project_state/task_packet.json`、`artifact_index.json`、`model_gate.json` 是否确实有必要；无必要则回退。
9. 最终 `lint-report`、`doctor`、`final-check`、`close-round` 是否全部重新运行并退出 0。
10. 确认本轮没有运行样本、IDA/Ghidra/debugger/harness campaign、solver、candidate search 或 runtime probe。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/final_gate_result.json`
- `project_state/rounds/round_20260612_rework4_final_gate_closeout_contract_v1/*`

允许回退上一轮无关改动：

- `reverse_agent/harness.py`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`

不允许修改：

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- raw local samples
- sample binaries
- solver/harness/IDA/Ghidra/debugger 功能逻辑
- 训练队列业务分类规则，除非只是为了修复 gate schema 字段名
- candidate validation outputs
- unrelated source modules
- unrelated tests

## 7. Tests

必须运行并完整记录 stdout/stderr/exit code：

```bash
pwd
powershell -NoProfile -Command "Test-Path F:\reverse-agent"
git rev-parse --show-toplevel
git status --short
git diff --name-only
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_local_reverse_training_review.py tests/test_local_reverse_training_status.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260612_rework4_final_gate_closeout_contract_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
git diff --name-only
```

验收条件：

- `command_plan.json` 不再出现 `kind: unknown`，或 final-check 明确允许并能完整匹配。
- `pytest_result.txt` 覆盖 report 中所有 `tests_ran`。
- `pytest_result` 中命令字符串不能用 `...` 替代真实命令。
- `command-plan --json` stdout 必须完整记录 commands array。
- `close-round` 成功生成 round manifest。
- archived report/pytest 与 live report/pytest 一致。
- `final_gate_result.json` 为 `PASSED`。
- `lint-report`、`doctor`、`final-check`、`close-round` 均不得 FAIL。
- report 的 `generated_artifacts` 必须覆盖本轮 gate 产物和 round archive。
- 只有以上条件全部满足，report 才能写 `SUCCESS + ACCEPTED`。

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

- 需要运行样本、solver、IDA/Ghidra/debugger 才能修复 gate。
- 需要读取完整 `solve_reports/`。
- 无法解释或回退 `harness.py` 等越界变更。
- `close-round` 仍无法生成有效 round manifest。
- `final-check` 仍为 `FAILED`。
- 只能通过降低 gate 校验强度来“假通过”。
- 需要修改 `.codex-skills/` 才能继续。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_project_state_mainline_clarity_rework_v2",
  "round_id": "round_20260615_project_state_mainline_clarity_rework_v2",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `project_state` / `project_gate` 主线清晰度实现中的两个阻塞问题：

1. 让真实 `archive_round()` 产出的 round manifest 或兼容 fallback 能正确支持 `latest_closed_round_id / latest_closed_decision_id / latest_accepted_round_id / latest_accepted_decision_id`。
2. 移除或改名 `task_packet_role=authoritative` 语义。所有主线下，当前执行权威都必须是 `project_state/decision_packet.md`；非工程主线的严格性应通过 artifact freshness requirement 表达，而不是说 `task_packet` 是 authoritative。

本轮仍然是 `engineering_branch`。不推进任何样本求解。

## 2. Current Evidence

当前上一轮报告为 `SUCCESS / ACCEPTED`，测试和 gate 记录完整，但审计发现实现与真实 archive manifest 不兼容，且 `task_packet_role` 命名违反长期规则。

`negative_results.json` 仍然约束样本求解路径：不要回旧 `sample_solver` blind search，不要只扩大 beam/budget，不要使用 `compare_semantics_agree=false` candidate，不要提交完整 `solve_reports`。本轮不得触碰这些方向。

## 3. Do Not Do

不要推进 `samplereverse`、`cpp1_2f6fcb63` 或任何样本求解。

不要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver search、旧 `sample_solver`、beam/topN/budget 扩张。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness 语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要清空、伪造或删除 `artifact_index.json` 中的 historical missing artifacts。

不要把 `task_packet.task` 重新定义为执行权威。

不要削弱 `reverse_solving / tool_integration / training_dataset` 下的 current artifact freshness 严格检查。

## 4. Files To Inspect

按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

必须重点检查：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`
- `project_state/rounds/round_20260615_project_state_mainline_clarity_v1/round_manifest.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`

## 5. Required Audit

执行前确认：

1. `decision_meta` parseable，`status=APPROVED`，`mainline=engineering_branch`。
2. `reverse-agent-iteration@v2` 在 registry 中存在且 active。
3. `decision_packet.md` 是执行权威；`task_packet.json` 只能提供压缩状态、历史线索或 advisory 信息。
4. 当前失败点不是 gate 缺失，而是实现语义缺陷。
5. `archive_round()` 真实输出路径必须被测试覆盖。
6. `latest accepted round` 不能依赖测试手写的 manifest 字段，必须对真实 manifest 生效。
7. 非工程主线的严格 artifact freshness 仍然保留，但不能通过 `task_packet_role=authoritative` 表达。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate.py`

允许生成：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_project_state_mainline_clarity_rework_v2/*`

只读，不得修改：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`

具体实现要求：

1. 修复 latest round metadata：
   - 优先方案：让 `_build_round_manifest()` 写入 `decision_id`、`report_id`、`report_status`、`acceptance_recommendation`。
   - 兼容方案：`_latest_closed_round_info()` 在 manifest 缺少字段时，从 archived `decision_packet.md` 和 `codex_execution_report.md` 读取 fallback。
   - 可以两者都做：新 archive 写字段，旧 archive fallback 读取归档文件。

2. 修复 task_packet role 表达：
   - 不得再输出 `task_packet_role=authoritative`。
   - 建议改为：
     - `execution_authority=decision_packet`
     - `task_packet_role=advisory` 或 `task_packet_role=state_input`
     - `artifact_freshness_requirement=strict` 用于 `reverse_solving / tool_integration / training_dataset`
     - `artifact_freshness_requirement=historical_external_notices_non_blocking` 用于 `engineering_branch`
   - 如果为了兼容保留旧字段，也必须避免其值为 `authoritative`，并在 CLI/JSON 中明确它不代表执行权威。

3. 测试要求：
   - 增加真实 `archive_round()` 生成 manifest 后，`_latest_closed_round_info()` 能识别 latest closed / latest accepted 的测试。
   - 增加旧 manifest 缺字段 fallback 测试。
   - 修改现有测试，禁止 `task_packet_role=authoritative`。
   - 增加测试证明非工程主线仍保留 strict artifact freshness requirement。
   - 保留 report/decision mismatch、pytest mismatch、forbidden path、scope violation 的失败测试。

## 7. Tests

必须记录命令、stdout/stderr、exit code 到 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_project_state_mainline_clarity_rework_v2
```

## 8. Stop Conditions

如果需要运行样本、runtime probe、debugger、hook、emulator、sidecar、solver 或 harness，停止并报告 `BLOCKED`。

如果只能通过删除或清空 historical missing artifacts 才能通过，停止并报告 `REWORK_REQUIRED`。

如果修复会让 `reverse_solving / tool_integration / training_dataset` 下的 current artifact freshness 检查变宽松，停止并报告 `REWORK_REQUIRED`。

如果 pytest、lint-report、report-summary、final-check 或 close-round 失败，不得提交 `SUCCESS` 报告。

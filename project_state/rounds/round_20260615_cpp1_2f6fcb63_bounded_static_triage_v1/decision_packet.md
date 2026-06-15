```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_cpp1_2f6fcb63_bounded_static_triage_v1",
  "round_id": "round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

从 `round_20260613_training_queue_static_triage_hygiene_v1` 之后恢复业务主线，对训练队列中下一个合理样本 `cpp1_2f6fcb63` 做有界静态 triage。

本轮只生成静态证据和状态登记，不求解、不生成候选、不运行样本。完成后应得到当前样本的 static triage artifact，并把该 artifact 以 current freshness 登记到 `artifact_index.json`。

## 2. Current Evidence

工程门禁支线已收口：`round_20260615_startup_status_baseline_consistency_guard_v1` 已 ACCEPTED，final gate 无 blocking / warnings，archive 已完成。

恢复点来自 `round_20260613_training_queue_static_triage_hygiene_v1`：当时队列中 `affineenc_333f8ca9` 已完成 static triage，PDF 文档不应进入可执行样本 triage，`cpp1_2f6fcb63` 被识别为下一个合理 PE 样本候选。

当前 `task_packet.json` 和 `current_state.json` 仍保留旧 `samplereverse` 信息，只能作为 historical/advisory。当前执行权威是 `project_state/decision_packet.md`。

## 3. Do Not Do

不要推进 `samplereverse`。

不要做动态执行、交互验证、候选生成或批量队列处理。

不要把 `cpp1_2f6fcb63` 标记为 solved。

不要重写旧 `affineenc_333f8ca9` 或 `affine_8cfebe03` 的证据语义。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`、training materials、raw sample 文件、solver/strategy/runtime 相关模块。

不要修改 live `project_state/decision_packet.md`。

不要把 `task_packet.task` 当作当前执行任务。

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

- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `project_state/local_reverse_inventory.json`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/project_state.py`
- `reverse_agent/project_gate.py`
- 直接相关测试

必要时只读恢复点：

- `project_state/rounds/round_20260613_training_queue_static_triage_hygiene_v1/decision_packet.md`
- `project_state/rounds/round_20260613_tool_integration_artifact_policy_closeout_v1/decision_packet.md`

## 5. Required Audit

执行前确认：

1. 当前 decision 是 `decision_20260615_cpp1_2f6fcb63_bounded_static_triage_v1`。
2. `reverse-agent-iteration@v2` 是 active skill。
3. 当前主线是 `tool_integration`。
4. `task_packet.json` 只是 advisory/state input。
5. `cpp1_2f6fcb63` 必须能由 inventory / training status / evaluation queue 交叉确认。
6. 先检查现有 static triage 工具和 artifact 登记流程，不能新建重复接口。
7. 如果已有 current static triage artifact，先审计 freshness/source_run，不重复生成。
8. 如果样本路径或静态工具不可用，生成 blocker diagnostic 并停止。

## 6. Implementation Scope

允许使用已有 static triage 工具对 `cpp1_2f6fcb63` 做一次有界静态提取。

允许生成或更新：

- `project_state/local_reverse_cpp1_2f6fcb63_static_triage.json` 或现有命名规范下的等价 artifact；
- `project_state/artifact_index.json`，只登记本轮 current artifact，不清空旧 missing/stale；
- `project_state/local_reverse_training_status.json`，只更新该样本的 static triage 状态；
- `project_state/local_reverse_evaluation_queue.json`，只做由现有生成器产生的有界更新；
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1/*`

允许最小源码/测试修改，仅限修复现有 static triage 或状态登记的明显 bug。不得新增平行工具体系。

## 7. Static Triage Requirements

静态 triage artifact 至少记录：

- `schema_version`
- `sample_id`
- `relative_path`
- `source_tool`
- `tool_status`
- `static_only: true`
- `runtime_validated: false`
- 文件 size / sha256 / format hints
- strings / functions / imports / xrefs / compare contexts / constants 中可稳定提取的摘要
- `hypotheses[]`，仅限静态假设
- `limitations[]`，说明未做动态验证、未做候选验证

若静态工具失败，生成 blocker diagnostic artifact，记录工具名、exit code、stdout/stderr 摘要、失败原因和下一步建议。

## 8. Tests

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
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_cpp1_2f6fcb63_bounded_static_triage_v1
```

如果运行 static triage 命令，也必须记录到 `pytest_result.txt` 和 `codex_report_summary.tests_ran`，并记录 exit code。

必须新增或确认测试覆盖：

1. `task_packet.task` 不覆盖本轮 decision；
2. historical sample missing artifacts 不阻塞当前 static triage closeout；
3. current static triage artifact missing/stale 仍会阻塞；
4. artifact_index 能登记本轮 current artifact；
5. 已完成 triage 的样本不会继续排在 static triage 队首；
6. decision immutability / startup baseline consistency / verified CLI coverage 不回退。

## 9. Stop Conditions

如果需要动态执行、交互验证或候选求解，停止并报告 `BLOCKED`。

如果需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`，停止并报告 `BLOCKED`。

如果 inventory 无法确认 `cpp1_2f6fcb63`，停止并报告 `BLOCKED`，不要改跑其他样本。

如果现有 static triage 工具不可用，生成 blocker diagnostic 并停止，不要新建重复工具接口。

如果需要修改 live `project_state/decision_packet.md` 才能通过，停止并报告 `REWORK_REQUIRED`。

如果 `command-plan` 不是 `PASSED`，不得写 `SUCCESS`。

如果 `report-summary / final-check / close-round` 任一 exit 非 0，不得写 `SUCCESS`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS`。

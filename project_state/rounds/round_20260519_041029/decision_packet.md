# DECISION_PACKET.md

本轮是 Phase 1 的小补丁任务：明确 `task_packet.json` 中“样本事实派生任务”和 `decision_packet.md` 中“当前 Codex 执行任务”的关系。

本轮不推进 `samplereverse` 逆向主线，不进入 Phase 2，也不实现 Phase 1B/1C/1E/1F 的完整内容。

## 1. Goal

解决当前 `task_packet.json` 与 `decision_packet.md` 的职责歧义。

当前 `project_state build` 会根据 `samplereverse` artifact 自动生成：

```text
 task_packet.task = Improve compare lhs last-writer instrumentation
 current_bottleneck.stage = compare_real_lhs_provenance_audit
 current_bottleneck.reason = instrumentation_incomplete
```

但 `decision_packet.md` 可以是架构改造任务，例如 Phase 1A/1D 返工。这样会导致 GPT/Codex 不清楚当前到底应执行：

```text
A. 样本逆向主线任务
B. project_state / harness 架构任务
```

本轮目标是在 `task_packet.json` 中增加轻量职责分离字段，使它能明确表达：

```text
1. task_packet.task 是从样本 artifact 派生出来的建议任务；
2. 当前 Codex 应执行的具体任务仍以 project_state/decision_packet.md 为准；
3. 当 decision_packet 是架构任务时，task_packet 不应被误读为本轮执行任务。
```

建议新增字段名可由 Codex 本地审计后确定，但语义必须覆盖：

```json
{
  "state_scope": "sample_state",
  "task_source": "derived_from_sample_artifacts",
  "derived_task": "Improve compare lhs last-writer instrumentation",
  "active_decision_packet": "project_state/decision_packet.md",
  "execution_scope": "decision_packet_controls_current_round"
}
```

如果字段名需要更简洁，也可使用：

```json
{
  "task_source": "derived_from_sample_artifacts",
  "active_decision_packet": "project_state/decision_packet.md"
}
```

但必须在测试和报告中说明其含义。

## 2. Current Evidence

上一轮 Phase 1A + Phase 1D 返工已接受为 `ACCEPTED_WITH_LIMITATIONS`：

- `round_manifest.json` 已改为记录 `source_path`、`archived_path`、`sha256`。
- `archive_round()` 已保留幂等逻辑。
- `tests/test_project_state.py` 已补充 manifest 路径语义测试。
- `project_state/pytest_result.txt` 已包含真实测试结果：`46 passed in 5.32s`。
- `codex_execution_report.md` 已明确说明 Phase 1B/1C/1E/1F 未完成。

但仍存在一个架构歧义：

```text
project_state/decision_packet.md = 当前 Codex 执行任务
project_state/task_packet.json = project_state build 根据样本 artifact 推导出的样本状态与建议任务
```

当前 `task_packet.json` 仍然显示：

```text
task = Improve compare lhs last-writer instrumentation
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = instrumentation_incomplete
```

这与架构改造任务可能不同。需要用字段明确区分，避免后续 GPT 或 Codex 误读。

## 3. Do Not Do

不要做以下事情：

- 不要进入 Phase 2。
- 不要实现 `lint-decision`。
- 不要实现 `latest_artifacts_v2` / freshness。
- 不要实现完整 `decision_meta` / `codex_report_summary`。
- 不要新增复杂状态机。
- 不要改 `reverse_agent/strategies/compare_aware_search.py`。
- 不要改 `reverse_agent/olly_scripts/*`。
- 不要运行 Base64/RC4 breakpoint probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要提交完整 `solve_reports/`。
- 不要默认读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不要把当前架构任务改写成新的 `samplereverse` 逆向任务。

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/task_packet.json
project_state/current_state.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可参考：

```text
docs/phase1_project_state_stability_plan.md
project_state/rounds/round_20260518_112941/round_manifest.json
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

实现前必须先确认并在 `codex_execution_report.md` 中说明：

1. `build_task_packet()` 当前如何从 `current_state` 推导 `task`。
2. `task_packet.task` 当前是否实际表示“样本 artifact 推导任务”，而不是“当前 Codex 执行任务”。
3. `decision_packet.md` 是否应继续作为当前 Codex 执行任务的唯一权威入口。
4. 新增字段是否会破坏已有测试或下游读取方。
5. 是否需要保留旧字段 `task`，以兼容已有 GPT/Codex 工作流。
6. 当前 `status_summary()` 是否需要显示新增字段，帮助命令行区分 derived task 和 active decision。

## 6. Implementation Scope

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许重新生成：

```text
project_state/artifact_index.json
project_state/current_state.json
project_state/negative_results.json
project_state/model_gate.json
project_state/task_packet.json
project_state/rounds/<new_round_id>/*
```

但本轮不要求改变 artifact 扫描逻辑，不要求压缩 current_state，不要求新增 artifact freshness。

### 6.1 task_packet 字段改造

在 `build_task_packet()` 输出中保留原有：

```json
{
  "task": "Improve compare lhs last-writer instrumentation"
}
```

同时新增职责分离字段，例如：

```json
{
  "state_scope": "sample_state",
  "task_source": "derived_from_sample_artifacts",
  "derived_task": "Improve compare lhs last-writer instrumentation",
  "active_decision_packet": "project_state/decision_packet.md",
  "execution_scope": "decision_packet_controls_current_round"
}
```

字段语义：

- `state_scope`: 当前状态包描述的是样本状态，暂定值 `sample_state`。
- `task_source`: `task` 的来源，当前应为 `derived_from_sample_artifacts`。
- `derived_task`: 与旧 `task` 相同，用于明确这是 artifact 派生任务。
- `active_decision_packet`: 当前 Codex 执行入口，固定为 `project_state/decision_packet.md`。
- `execution_scope`: 当前轮执行权威来自 decision packet，不来自自动派生 task。

如果 Codex 认为字段过多，可保留最小集合：

```json
{
  "task_source": "derived_from_sample_artifacts",
  "active_decision_packet": "project_state/decision_packet.md"
}
```

但必须保留 `task` 旧字段兼容。

### 6.2 status_summary 输出补充

`python -m reverse_agent.project_state status` 当前输出 `task` 和 `expected_gpt_output`。

建议补充显示：

```text
task_source: derived_from_sample_artifacts
active_decision_packet: project_state/decision_packet.md
execution_scope: decision_packet_controls_current_round
```

如果实现范围要更小，至少让 `status_summary()` 返回这些字段，并补测试即可。

### 6.3 测试要求

在 `tests/test_project_state.py` 中新增或补充：

1. `test_task_packet_distinguishes_derived_task_from_active_decision`
   - 验证 `task` 仍存在。
   - 验证 `derived_task == task`。
   - 验证 `task_source == derived_from_sample_artifacts`。
   - 验证 `active_decision_packet == project_state/decision_packet.md`。
   - 验证 `execution_scope == decision_packet_controls_current_round`。

2. `test_status_summary_includes_task_source_and_active_decision`
   - 验证 `status_summary()` 或 CLI `status` 能暴露新增字段。

3. 确认旧测试不需要大规模重写。

### 6.4 更新 codex_execution_report.md

报告必须说明：

- 本轮是 Phase 1 小补丁，不是 Phase 1B/C/E/F。
- 新增字段的语义。
- 为什么保留旧 `task` 字段。
- `decision_packet.md` 是否仍为当前 Codex 执行入口。
- 运行了哪些测试，结果是什么。
- 是否重新执行了 `project_state build` 和 `archive-round`。

## 7. Tests

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
```

如果本地有 `solve_reports`，再运行：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r3
python -m reverse_agent.project_state status
python -m reverse_agent.project_state archive-round
```

测试输出写入：

```text
project_state/pytest_result.txt
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

1. 需要大规模重构 `build_task_packet()`。
2. 需要修改 `build_artifact_index()` 或 artifact 扫描逻辑。
3. 需要修改 reverse strategy 或 runtime probe。
4. 新增字段会破坏旧 `task_packet.json` 消费方。
5. 无法让 `decision_packet.md` 继续作为当前 Codex 执行入口。
6. 测试需要大规模重写。

## Acceptance Criteria

本轮可接受的条件：

1. `task_packet.json` 保留旧 `task` 字段。
2. `task_packet.json` 新增字段明确说明 `task` 是 artifact 派生任务。
3. `task_packet.json` 明确指向 `project_state/decision_packet.md` 作为当前 Codex 执行入口。
4. `status_summary()` 或 CLI `status` 能暴露新增字段。
5. `tests/test_project_state.py` 覆盖新增字段。
6. `project_state/pytest_result.txt` 包含真实测试结果。
7. 不进入 Phase 2，不改逆向主策略。

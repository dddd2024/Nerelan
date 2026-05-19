# DECISION_PACKET.md

本轮进入 Phase 1C：增强 `artifact_index.json` 的 provenance / freshness 表达能力。

本轮不推进 `samplereverse` 逆向主线，不进入 Phase 1E/1F，不进入 Phase 2，不实现 `lint-decision`，不修改逆向策略。

## 1. Goal

实现 Phase 1C 的最小闭环：让 `artifact_index.json` 不只记录 artifact 路径，还能稳定回答：

```text
这个 artifact 来自哪个 harness run？
是否来自当前 selected/latest run？
文件是否存在？
文件大小是多少？
sha256 是什么？
modified_at 是什么？
这个 artifact 是 current / stale / missing / unknown？
```

本轮目标是新增兼容字段，不破坏现有 `latest_artifacts`：

```json
{
  "latest_artifacts_v2": {
    "compare_real_lhs_provenance_audit": {
      "path": "...",
      "kind": "compare_real_lhs_provenance_audit",
      "source_run": "sr_lhs_last_writer_health_fix_20260518_r3",
      "modified_at": "2026-05-18T09:47:21Z",
      "size_bytes": 39569,
      "sha256": "...",
      "freshness": "current"
    }
  }
}
```

本轮只做 artifact index 的 provenance / freshness。不要进入 Phase 1E，不要实现 `lint-decision`，不要进入 Phase 2。

## 2. Current Evidence

当前 `task_packet.json` 仍描述 `samplereverse` 的样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明 `task_packet.task` 不等于本轮 Codex 执行任务，当前执行入口仍是 `decision_packet.md`。

当前 `current_state.json` 记录的状态身份为：

```text
round_id = round_20260519_063549
state_build_id = state_20260519_063549_cf4670d47eb6
state_digest = cf4670d47eb6f2fbbe7106d2f4927e6f7aa2fb125dfe77c776c80d4dae6abfc6
source_harness_run = sr_lhs_last_writer_health_fix_20260518_r3
workflow_status = REPORT_AVAILABLE
```

Codex 最新报告显示 Phase 1B-fix 已完成：`task_packet.json` 不再缓存完整 `handoff_status`，`status_summary()` 动态读取 live decision/report，并且测试为 `57 passed in 5.11s`。

当前 `artifact_refs` 中混合了当前 harness run 与旧 legacy artifact 路径，例如当前 run 的 `compare_real_lhs_provenance_audit`、`compare_probe`、`summary`，以及旧的 `frontier_summary`、`function_semantic_audit`、`base64_rc4_static_point_discovery` 等。这正是需要 Phase 1C 的原因：GPT 需要知道每个 artifact 的来源和新鲜度，而不能只看路径。

## 3. Do Not Do

不要做以下事情：

```text
不要进入 Phase 2。
不要实现 lint-decision。
不要进入 Phase 1E。
不要进入 Phase 1F。
不要修改 reverse_agent/harness.py 主流程。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要运行 Base64/RC4 breakpoint probe。
不要回旧 sample_solver。
不要扩大 beam、topN、budget、timeout、frontier iteration。
不要提交完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
不要把本轮架构任务改写成 samplereverse 逆向任务。
不要删除旧 latest_artifacts 字段。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/artifact_index.json
project_state/task_packet.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可参考：

```text
docs/phase1_project_state_stability_plan.md
project_state/rounds/round_20260519_063549/round_manifest.json
```

不要默认读取完整 `solve_reports/`。如果需要 artifact 文件元数据，只能通过当前 `artifact_index` 已索引路径或测试 fixture 有界构造。

## 5. Required Audit

Codex 实现前必须先确认并在 `codex_execution_report.md` 中说明：

```text
1. build_artifact_index() 当前如何选择 latest_harness_run。
2. latest_artifacts 当前是如何从扫描结果中选出路径的。
3. recent_artifacts 当前已经有哪些元数据字段。
4. run_name 参数是否会限制 harness run 选择。
5. artifact_refs 为什么会混入 legacy tool_artifacts 和当前 harness run artifacts。
6. 是否可以在不改变旧 latest_artifacts 的情况下新增 latest_artifacts_v2。
7. 是否已有 sha256 工具函数可复用。
8. freshness 的最小判定规则应该如何实现。
```

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

### 6.1 新增 latest_artifacts_v2

保留旧字段：

```json
"latest_artifacts": {
  "summary": "solve_reports\\harness_runs\\...\\summary.json"
}
```

新增字段：

```json
"latest_artifacts_v2": {
  "summary": {
    "path": "solve_reports\\harness_runs\\...\\summary.json",
    "kind": "summary",
    "source_run": "sr_lhs_last_writer_health_fix_20260518_r3",
    "modified_at": "2026-05-18T09:47:21Z",
    "size_bytes": 948,
    "sha256": "...",
    "freshness": "current"
  }
}
```

### 6.2 freshness 最小规则

本轮只实现最小规则：

```text
current:
  artifact 路径位于 latest_harness_run 下，或位于显式 --run-name 指定 run 下。

stale:
  artifact 存在，但不属于 latest_harness_run / selected run。

missing:
  artifact key 存在，但 path 为 null 或文件不存在。

unknown:
  无法判断 source_run 或路径结构不符合预期。
```

不要在本轮做复杂 `accepted_by_decision_id` 或 `supersedes` 机制。

### 6.3 source_run 识别

建议规则：

```text
如果路径形如 solve_reports/harness_runs/<run_name>/...
  source_run = <run_name>

如果路径来自 solve_reports/tool_artifacts/...
  source_run = legacy_tool_artifacts

如果无法识别：
  source_run = ""
```

### 6.4 task_packet 是否使用 v2

本轮不要大改 `task_packet.artifact_refs`。可以保持它继续使用旧 path-only 结构。

可选：在 `artifact_index.json` 中提供 `latest_artifacts_v2`，让 GPT 审查时读取。不要强制所有下游立即迁移。

### 6.5 status_summary 可选增强

如果实现简单，可以在 `status_summary()` 中增加：

```text
artifact_index_v2_count
current_artifact_count
stale_artifact_count
missing_artifact_count
```

但这不是本轮必须项。优先保证 `artifact_index.json` 的 v2 字段和测试稳定。

## 7. Tests

必须新增或修改 `tests/test_project_state.py`，覆盖：

```text
test_artifact_index_v2_contains_source_run_and_freshness
test_artifact_from_selected_run_marked_current
test_legacy_tool_artifact_marked_stale_or_unknown
test_missing_artifact_marked_missing
test_artifact_index_preserves_legacy_latest_artifacts
test_artifact_index_v2_records_size_modified_at_and_sha256
```

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

```text
1. 需要大规模重构 build_artifact_index()。
2. 需要修改 reverse strategy 或 runtime probe。
3. 需要修改 harness.py 主流程。
4. 需要读取完整 solve_reports 才能完成。
5. latest_artifacts_v2 会破坏旧 latest_artifacts 消费方。
6. freshness 规则无法在当前路径结构下可靠判断。
7. sha256 计算导致明显性能问题。
8. 测试需要大规模重写。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. artifact_index.json 保留旧 latest_artifacts。
2. artifact_index.json 新增 latest_artifacts_v2。
3. latest_artifacts_v2 至少包含 path、kind、source_run、modified_at、size_bytes、sha256、freshness。
4. 当前 selected/latest harness run 下的 artifact 标记为 current。
5. legacy 或非 selected run artifact 不误标为 current。
6. missing artifact 能标记为 missing。
7. tests/test_project_state.py 覆盖上述行为。
8. project_state/pytest_result.txt 包含真实测试结果。
9. 不进入 Phase 1E/1F/Phase 2，不改逆向主策略。
```

# DECISION_PACKET.md

本轮是 Phase 1B 的收口补丁：消除 `task_packet.json` 中缓存 `handoff_status` 后可能 stale 的风险。

本轮不推进 `samplereverse` 逆向主线，不进入 Phase 1C/1E/1F，不进入 Phase 2，不实现 artifact freshness，也不实现 `lint-decision`。

## 1. Goal

修复上一轮 Phase 1B 实现中的状态一致性风险。

上一轮已经完成：

```text
1. 支持解析 decision_packet.md 顶部 decision_meta。
2. 支持解析 codex_execution_report.md 顶部 codex_report_summary。
3. 缺失 meta 不会误判为 APPROVED / SUCCESS。
4. 非法 JSON meta 不会导致 status/build 崩溃。
5. status_summary / CLI status 能暴露 decision/report 状态。
```

但审计发现：`build_project_state()` 会把 `build_handoff_status(state_dir)` 的结果固化写入 `task_packet.json["handoff_status"]`。由于 Codex 的常见执行顺序是：

```text
1. build project_state
2. 修改代码
3. 跑测试
4. 写 codex_execution_report.md
5. 写 pytest_result.txt
6. archive-round
```

所以 `task_packet.json["handoff_status"]` 很容易在最终 `codex_execution_report.md` 写入后变成过期快照。

当前已经出现具体不一致：

```text
task_packet.json.based_on_state_digest = e81940ea11f80978efeecdcb103e03ab80c18518931ad6016d01db884597e749

task_packet.json.handoff_status.decision.based_on_state_digest = d8b41081b53fb0657f411ebf76c9c6a07942d33fdfdc05d7f14009645dfdf9c6

task_packet.json.handoff_status.codex_report.round_id = round_20260519_061910

codex_execution_report.md.codex_report_summary.round_id = round_20260519_062046
```

本轮目标是：

```text
不要让 task_packet.json 缓存容易过期的完整 handoff_status。
status_summary() / CLI status 继续动态读取 live decision_packet.md 和 codex_execution_report.md。
```

推荐最小实现：

```text
1. 从 build_project_state() 中移除 task_packet["handoff_status"] = build_handoff_status(state_dir)。
2. task_packet.json 继续保留 active_decision_packet / task_source / execution_scope 等稳定字段。
3. status_summary() 继续动态调用 build_handoff_status(state_dir)。
4. CLI status 继续打印 decision/report 状态。
5. 测试确认 task_packet.json 不再包含 handoff_status，避免 stale snapshot。
```

如果 Codex 判断必须保留 `handoff_status` 字段，则必须改为带来源 digest 的可校验快照：

```json
{
  "handoff_status": {...},
  "handoff_status_sources": {
    "decision_packet.md": {"sha256": "..."},
    "codex_execution_report.md": {"sha256": "..."}
  },
  "handoff_status_freshness": "current|stale|unknown"
}
```

但本轮优先选择“移除 task_packet 中的 cached handoff_status”，因为这更小、更稳、更符合低 token 状态包定位。

## 2. Current Evidence

上一轮 Phase 1B 改动已经完成解析原型：

- `reverse_agent/project_state.py` 新增：
  - `extract_markdown_json_block()`
  - `read_decision_meta()`
  - `read_codex_report_summary()`
  - `build_handoff_status()`
- `status_summary()` 和 CLI `status` 已动态暴露：
  - `decision_status`
  - `decision_id`
  - `decision_based_on_state_digest`
  - `decision_parse_error`
  - `report_status`
  - `report_acceptance_recommendation`
  - `report_id`
  - `report_based_on_decision_id`
  - `report_parse_error`
- `tests/test_project_state.py` 已覆盖合法 meta、缺失 meta、非法 JSON、模板文件和 status 输出。
- 最新测试记录：`55 passed in 4.94s`。

但当前 `task_packet.json` 中固化的 `handoff_status` 已经与 live Markdown 文件存在不一致，说明该字段作为缓存不可靠。

本轮不是重做 Phase 1B，而是修复 Phase 1B 的状态同步风险。

## 3. Do Not Do

不要做以下事情：

- 不要进入 Phase 1C。
- 不要实现 `latest_artifacts_v2` / artifact freshness。
- 不要进入 Phase 1E。
- 不要实现 `lint-decision`。
- 不要进入 Phase 1F。
- 不要新增 `project_state/schema.md`，除非只是极小说明且不影响代码范围。
- 不要进入 Phase 2。
- 不要修改 `reverse_agent/harness.py`。
- 不要修改 `reverse_agent/strategies/compare_aware_search.py`。
- 不要修改 `reverse_agent/olly_scripts/*`。
- 不要运行 Base64/RC4 breakpoint probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要提交完整 `solve_reports/`。
- 不要默认读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不要把本轮架构收口任务改写成新的 `samplereverse` 逆向任务。

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/task_packet.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

可参考：

```text
project_state/rounds/round_20260519_062046/round_manifest.json
docs/phase1_project_state_stability_plan.md
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

1. `build_project_state()` 当前何时调用 `build_handoff_status(state_dir)`。
2. `task_packet["handoff_status"]` 是在写入最终 `codex_execution_report.md` 之前还是之后生成。
3. `status_summary()` 是否已经动态读取 live decision/report。
4. 移除 `task_packet["handoff_status"]` 是否会破坏现有测试。
5. 如果保留 `handoff_status`，是否能够通过 source sha256 检测 stale。
6. 当前 `task_packet.json` 是否仍应保留 `active_decision_packet`、`task_source`、`execution_scope` 等职责分离字段。

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

本轮推荐实现方案：

### 6.1 移除 task_packet 中的 cached handoff_status

在 `build_project_state()` 中删除或避免执行：

```python
task_packet["handoff_status"] = build_handoff_status(state_dir)
```

保留：

```json
{
  "active_decision_packet": "project_state/decision_packet.md",
  "task_source": "derived_from_sample_artifacts",
  "execution_scope": "decision_packet_controls_current_round",
  "expected_gpt_output": "project_state/decision_packet.md"
}
```

### 6.2 status_summary 继续动态读取

`status_summary()` 应继续调用：

```python
handoff_status = build_handoff_status(state_dir)
```

并继续输出：

```text
decision_status
decision_id
decision_based_on_state_digest
decision_parse_error
report_status
report_acceptance_recommendation
report_id
report_based_on_decision_id
report_parse_error
```

### 6.3 测试要求

在 `tests/test_project_state.py` 中新增或修改测试：

1. `test_task_packet_does_not_cache_handoff_status`
   - `build_project_state()` 后读取 `task_packet.json`。
   - 断言不包含完整 `handoff_status`。
   - 断言仍包含 `active_decision_packet`、`task_source`、`execution_scope`。

2. `test_status_summary_reads_live_handoff_status_after_task_packet_build`
   - 先 `build_project_state()`。
   - 再修改 `codex_execution_report.md` 的 `codex_report_summary`。
   - 不重新 build。
   - 调用 `status_summary()`。
   - 断言 `report_status` 反映 live report，而不是旧 task_packet 快照。

3. 如果现有测试依赖 `task_packet["handoff_status"]`，应改为测试 `status_summary()` 的动态 handoff 状态。

### 6.4 更新报告

`codex_execution_report.md` 必须说明：

- 本轮是 Phase 1B-fix。
- 为什么不再把完整 `handoff_status` 固化进 `task_packet.json`。
- `status_summary()` 仍然动态读取 live decision/report。
- 哪些测试被新增或修改。
- 运行了哪些命令，结果是什么。
- Phase 1C/1E/1F/Phase 2 仍未实现。

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

1. 移除 `task_packet["handoff_status"]` 会破坏多个下游调用方且无法兼容。
2. `status_summary()` 无法动态读取 live decision/report。
3. 需要大规模重构 `build_project_state()`。
4. 需要修改 artifact 扫描逻辑。
5. 需要修改 reverse strategy 或 runtime probe。
6. 需要进入 Phase 1C/1E/1F 或 Phase 2 才能完成。
7. 测试需要大规模重写。

## Acceptance Criteria

本轮可接受的条件：

1. `task_packet.json` 不再包含完整 cached `handoff_status`，或能明确检测其 freshness；优先前者。
2. `task_packet.json` 仍保留 `active_decision_packet`、`task_source`、`execution_scope`。
3. `status_summary()` / CLI `status` 继续动态暴露 decision/report 状态。
4. 修改 live `codex_execution_report.md` 后，不重新 build 也能让 `status_summary()` 读到新 report 状态。
5. `tests/test_project_state.py` 覆盖上述行为。
6. `project_state/pytest_result.txt` 包含真实测试结果。
7. 不进入 Phase 1C/1E/1F，不进入 Phase 2，不改逆向主策略。

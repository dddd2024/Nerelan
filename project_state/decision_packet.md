# DECISION_PACKET.md

本轮进入 Phase 1B：为 `decision_packet.md` 和 `codex_execution_report.md` 增加轻量有效性标记与解析能力。

本轮不推进 `samplereverse` 逆向主线，不进入 Phase 2，不实现 artifact freshness，也不实现 `lint-decision`。

## 1. Goal

实现 Phase 1B 的最小闭环：让 `project_state` 能判断当前 `decision_packet.md` 和 `codex_execution_report.md` 是否是模板、草稿、已批准任务、成功报告、部分成功报告、失败报告或阻塞报告，并能把它们与当前 `state_build_id/state_digest/round_id` 建立弱绑定。

本轮目标只包括：

1. 在 `decision_packet.md` 顶部支持可选 fenced JSON 元信息块 `decision_meta`。
2. 在 `codex_execution_report.md` 顶部支持可选 fenced JSON 元信息块 `codex_report_summary`。
3. 在 `reverse_agent/project_state.py` 中新增解析函数，能从 Markdown 中提取这些 JSON 元信息。
4. 当元信息不存在时，必须向后兼容，不能破坏当前 Markdown 文件。
5. `status_summary()` 或 `task_packet.json/current_state.json` 至少暴露 decision/report 的有效性状态，帮助 GPT 判断是否能基于当前文件继续协作。
6. `tests/test_project_state.py` 覆盖模板、缺失 meta、合法 meta、非法 JSON、旧文件兼容等场景。
7. 更新 `codex_execution_report.md`，说明本轮 Phase 1B 的实际完成情况和测试结果。

本轮完成后，GPT/Codex 应能回答：

```text
当前 decision_packet.md 是 TEMPLATE_ONLY / DRAFT / APPROVED / SUPERSEDED / UNKNOWN 中哪一种？
当前 codex_execution_report.md 是 TEMPLATE_ONLY / SUCCESS / PARTIAL / FAILED / BLOCKED / UNKNOWN 中哪一种？
decision 是否声明 based_on_state_digest？
report 是否声明 based_on_decision_id？
缺少 meta 时是否能安全降级，而不是误判为已批准或已完成？
```

## 2. Current Evidence

已完成并接受的 Phase 1 子项：

1. Phase 1A：`project_state` 身份锚点
   - `schema_version = 2`
   - `state_build_id`
   - `round_id`
   - `state_digest`
   - `based_on_state_digest`
   - `workflow_status/current_owner/review_status`

2. Phase 1D：`archive-round` 可回放基础
   - `round_manifest.json`
   - `source_path`
   - `archived_path`
   - `sha256`
   - archive 幂等测试

3. Phase 1 小补丁：`task_packet` 职责分离
   - `state_scope = sample_state`
   - `task_source = derived_from_sample_artifacts`
   - `derived_task == task`
   - `active_decision_packet = project_state/decision_packet.md`
   - `execution_scope = decision_packet_controls_current_round`

当前仍未完成：

```text
Phase 1B：decision/report 有效性标记
Phase 1C：artifact_index provenance / freshness
Phase 1E：negative_results 最小门禁
Phase 1F：schema 文档固化
Phase 2：harness 可复现/可恢复/可比较
```

当前 `task_packet.json` 仍可描述 `samplereverse` 的派生任务，这是预期行为；当前 Codex 执行入口以本文件 `project_state/decision_packet.md` 为准。

## 3. Do Not Do

不要做以下事情：

- 不要进入 Phase 2。
- 不要实现 `lint-decision`。
- 不要实现 `latest_artifacts_v2` / freshness。
- 不要重构 artifact 扫描逻辑。
- 不要新增复杂状态机。
- 不要引入数据库、Redis、队列、worker manager、lease/heartbeat。
- 不要修改 `reverse_agent/strategies/compare_aware_search.py`。
- 不要修改 `reverse_agent/olly_scripts/*`。
- 不要运行 Base64/RC4 breakpoint probe。
- 不要回旧 `sample_solver`。
- 不要扩大 beam、topN、budget、timeout、frontier iteration。
- 不要提交完整 `solve_reports/`。
- 不要默认读取完整 `PROJECT_PROGRESS_LOG.txt`。
- 不要把本轮架构任务改写成新的 `samplereverse` 逆向任务。
- 不要要求旧 Markdown 文件必须立刻带 meta；必须兼容缺失 meta 的情况。

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
project_state/rounds/<latest_round>/round_manifest.json
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

1. 当前 `DECISION_PACKET_TEMPLATE` 和 `CODEX_EXECUTION_REPORT_TEMPLATE` 的格式。
2. 当前 `new_round()` 是否会生成模板 decision/report 文件。
3. 当前 `status_summary()` 能读取哪些状态。
4. 是否已有 Markdown fenced code block 解析工具；如果没有，新增最小解析函数即可。
5. 旧 `decision_packet.md` / `codex_execution_report.md` 缺少 meta 时应如何降级。
6. meta 是否应该写入当前文件，还是只先支持解析。建议本轮可以更新当前文件的 meta，但不要强制所有历史 round 都补 meta。
7. `decision_id/report_id` 是否应直接由 meta 给出；若未给出，是否可由文件 sha256 派生。第一轮可只解析，不强制生成。

## 6. Implementation Scope

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/decision_packet.md
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

但不要修改逆向策略，不要修改 harness 主流程，不要实现 Phase 1C/1E/Phase 2。

### 6.1 decision_meta 格式

在 `decision_packet.md` 顶部支持如下 fenced JSON：

````markdown
```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_<sha256_or_short_id>",
  "based_on_state_build_id": "state_...",
  "based_on_state_digest": "...",
  "round_id": "round_...",
  "status": "APPROVED",
  "created_by": "web_gpt",
  "created_at": "2026-05-19T00:00:00Z"
}
```
````

允许状态枚举：

```text
TEMPLATE_ONLY
DRAFT
APPROVED
SUPERSEDED
UNKNOWN
```

最小实现要求：

- 能解析合法 `decision_meta`。
- 缺失 `decision_meta` 时返回 `status = UNKNOWN` 或 `TEMPLATE_ONLY`，但不得误判为 `APPROVED`。
- 非法 JSON 时返回可审计错误状态，不能抛异常导致 build/status 整体失败。
- 不要求本轮实现强一致校验，只需暴露状态和字段。

### 6.2 codex_report_summary 格式

在 `codex_execution_report.md` 顶部支持如下 fenced JSON：

````markdown
```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_<sha256_or_short_id>",
  "round_id": "round_...",
  "based_on_decision_id": "decision_...",
  "status": "PARTIAL",
  "acceptance_recommendation": "NEEDS_REVIEW",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": ""
}
```
````

允许 `status` 枚举：

```text
TEMPLATE_ONLY
SUCCESS
PARTIAL
FAILED
BLOCKED
UNKNOWN
```

允许 `acceptance_recommendation` 枚举：

```text
ACCEPTED
REWORK_REQUIRED
BLOCKED
NEEDS_REVIEW
UNKNOWN
```

最小实现要求：

- 能解析合法 `codex_report_summary`。
- 缺失 summary 时返回 `status = UNKNOWN` 或 `TEMPLATE_ONLY`，不得误判为 `SUCCESS`。
- 非法 JSON 时返回错误状态，不应导致 `project_state build/status` 崩溃。
- 不要求本轮自动判断报告内容真伪，只做 meta 解析和状态暴露。

### 6.3 project_state.py 建议函数

可新增类似函数，名称由 Codex 审计后决定：

```python
extract_markdown_json_block(text: str, block_name: str) -> dict[str, Any]
read_decision_meta(state_dir: Path) -> dict[str, Any]
read_codex_report_summary(state_dir: Path) -> dict[str, Any]
build_handoff_status(state_dir: Path) -> dict[str, Any]
```

建议输出结构：

```json
{
  "decision": {
    "status": "APPROVED",
    "decision_id": "...",
    "based_on_state_digest": "...",
    "parse_error": null
  },
  "codex_report": {
    "status": "PARTIAL",
    "acceptance_recommendation": "NEEDS_REVIEW",
    "report_id": "...",
    "based_on_decision_id": "...",
    "parse_error": null
  }
}
```

第一轮可以只把该结构放入 `status_summary()`，或写入 `task_packet.json` 的一个字段，例如：

```json
{
  "handoff_status": {
    "decision_status": "APPROVED",
    "report_status": "PARTIAL",
    "acceptance_recommendation": "NEEDS_REVIEW"
  }
}
```

如果写入 JSON 状态会引起额外复杂度，先实现 `status_summary()` 暴露即可。

### 6.4 测试要求

在 `tests/test_project_state.py` 中新增或补充：

1. `test_extract_decision_meta_json`
   - 合法 `decision_meta` 能解析。

2. `test_extract_codex_report_summary_json`
   - 合法 `codex_report_summary` 能解析。

3. `test_missing_decision_meta_is_not_approved`
   - 缺失 meta 不得返回 `APPROVED`。

4. `test_missing_codex_report_summary_is_not_success`
   - 缺失 summary 不得返回 `SUCCESS`。

5. `test_invalid_markdown_json_meta_is_reported_without_crashing`
   - 非法 JSON 返回 parse error，build/status 不崩。

6. `test_status_summary_exposes_decision_and_report_status`
   - `status_summary()` 或 CLI `status` 能暴露 decision/report 状态。

旧测试不能大规模重写。

### 6.5 更新当前 decision/report 文件

本轮可以选择给当前 `decision_packet.md` 顶部添加 `decision_meta`，但要注意：

- 当前文件由 GPT 生成，因此 `created_by` 可写 `web_gpt`。
- `status` 可写 `APPROVED`，因为用户已要求执行下一步计划。
- `based_on_state_digest` 应使用当前 `task_packet.json.based_on_state_digest`。
- 如果不确定当前 digest，Codex 应在本地读取 `task_packet.json` 后再写。

本轮也可以给 `codex_execution_report.md` 顶部添加或更新 `codex_report_summary`，但报告状态应反映本轮实际执行结果，未执行前不要预填 `SUCCESS`。

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

1. 需要大规模重构 Markdown 文件格式。
2. 需要大规模重构 `build_project_state()` 或 `build_task_packet()`。
3. 需要修改 artifact 扫描逻辑。
4. 需要修改 reverse strategy 或 runtime probe。
5. 新增 meta 会破坏旧 Markdown 消费方。
6. 不能在缺失 meta 时安全降级。
7. 测试需要大规模重写。

## Acceptance Criteria

本轮可接受的条件：

1. 支持解析 `decision_meta`。
2. 支持解析 `codex_report_summary`。
3. 缺失 meta 不会被误判为 approved/success。
4. 非法 JSON meta 不会导致 build/status 崩溃。
5. `status_summary()` 或 CLI `status` 能暴露 decision/report 状态。
6. `tests/test_project_state.py` 覆盖上述行为。
7. `project_state/pytest_result.txt` 包含真实测试结果。
8. 不进入 Phase 2，不改逆向主策略，不实现 artifact freshness 或 lint-decision。

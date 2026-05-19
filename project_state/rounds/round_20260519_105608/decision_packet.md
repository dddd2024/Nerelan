```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1d_lint_decision_min_gate_20260519",
  "round_id": "round_20260519_085626",
  "based_on_state_build_id": "state_20260519_085626_acd12be00935",
  "based_on_state_digest": "acd12be0093533d1bb86b1bec1959a3d138e0a48d52cf6bb8f8b1194473eeb8c",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 1D：实现最小 `lint-decision` 门禁。

本轮仍属于工程架构改造支线，不推进 `samplereverse` 逆向主线，不运行 runtime probe，不进入 Phase 2，不做重型 workflow runtime。

## 1. Goal

实现一个最小、可测试、fail-soft 的 decision 门禁，用于在 Codex 执行前快速判断当前 `project_state/decision_packet.md` 是否可执行。

本轮目标是新增：

```text
python -m reverse_agent.project_state lint-decision
```

最小检查项：

```text
1. decision_packet.md 必须存在。
2. decision_meta 必须存在。
3. decision_meta.status 必须是 APPROVED。
4. decision_id 必须非空。
5. based_on_state_build_id 必须非空。
6. based_on_state_digest 必须非空。
7. based_on_state_digest 应能与当前 current_state.json 的 state_digest 对比。
8. 如果 digest 不匹配，不要直接崩溃；输出明确 stale/mismatch 诊断，并返回非 0。
9. 如果当前 task_packet.execution_scope 是 decision_packet_controls_current_round，则明确提示当前执行权威来自 decision_packet.md。
10. lint 输出必须是人类可读文本；可选提供 JSON summary，但不要做复杂 schema。
```

本轮只实现 decision 侧最小门禁，不实现完整 policy engine，不实现 negative_results 语义解析，不实现自动修复。

## 2. Current Evidence

当前任务主线：工程架构改造支线。

当前 `task_packet.json` 仍显示样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明 `task_packet.task` 只是 derived_task，本轮 Codex 执行权威仍来自 `project_state/decision_packet.md`。

当前状态身份：

```text
round_id = round_20260519_085626
state_build_id = state_20260519_085626_acd12be00935
state_digest = acd12be0093533d1bb86b1bec1959a3d138e0a48d52cf6bb8f8b1194473eeb8c
source_harness_run = sr_lhs_last_writer_health_fix_20260518_r3
```

上一轮 Phase 1C-fix 已经完成：

```text
decision_status: APPROVED
report_status: SUCCESS
report_based_on_decision_id: decision_phase1c_handoff_traceability_fix_20260519
decision_report_id_match: True
```

因此现在可以在此基础上实现最小 `lint-decision`。

artifact freshness 现状：

```text
latest_artifacts_v2 已存在。
compare_probe / compare_probe_log / compare_real_lhs_provenance_audit 等当前 run artifact 标记为 current。
frontier_summary / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
多个未生成 artifact 标记为 missing。
```

这些 artifact 只用于说明状态，不是本轮要消费的逆向证据。

## 3. Do Not Do

不要做以下事情：

```text
不要推进 samplereverse 解题。
不要运行 Base64/RC4 breakpoint probe。
不要运行任何逆向 runtime sidecar。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要修改 reverse_agent/harness.py 主流程。
不要扩大 beam、topN、budget、timeout、frontier iteration。
不要回旧 sample_solver。
不要提交完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
不要实现完整 lint framework。
不要实现复杂 policy engine。
不要实现自动修改 decision_packet.md。
不要实现 GitHub Actions / CI workflow。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要删除旧 latest_artifacts。
不要破坏旧 project_state 字段兼容性。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/decision_packet.md
project_state/current_state.json
project_state/task_packet.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时参考：

```text
project_state/artifact_index.json
project_state/rounds/round_20260519_085626/round_manifest.json
project_state/rounds/round_20260519_085626/git_diff.patch
docs/phase1_project_state_stability_plan.md
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

```text
1. main() 当前有哪些 subcommand。
2. status subcommand 当前如何读取 decision/report 状态。
3. read_decision_meta() 当前对 missing / invalid / TEMPLATE_ONLY / APPROVED 的行为。
4. status_summary() 当前是否已经暴露 decision_status、decision_id、decision_based_on_state_digest。
5. current_state.json 中 state_build_id / state_digest 的字段来源。
6. task_packet.json 中 execution_scope / active_decision_packet 的字段来源。
7. 上一轮 handoff_consistency / decision_report_id_match 是否已经实现。
8. lint-decision 是否可以复用 read_decision_meta()，避免重复解析 Markdown。
9. digest mismatch 应该返回非 0，但不能破坏 status/build/archive-round。
10. 是否已有测试可复用，避免重复造大型 fixture。
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

可选修改：

```text
docs/phase1_project_state_stability_plan.md
```

不要修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/*
reverse_agent/harness.py
```

### 6.1 lint-decision 行为

新增函数建议：

```text
lint_decision(state_dir: Path) -> dict[str, Any]
```

返回结构建议：

```json
{
  "ok": true,
  "errors": [],
  "warnings": [],
  "decision_id": "...",
  "decision_status": "APPROVED",
  "based_on_state_build_id": "...",
  "based_on_state_digest": "...",
  "current_state_build_id": "...",
  "current_state_digest": "...",
  "execution_scope": "decision_packet_controls_current_round",
  "active_decision_packet": "project_state/decision_packet.md"
}
```

最小错误条件：

```text
decision_meta missing -> error
decision_status != APPROVED -> error
decision_id empty -> error
based_on_state_build_id empty -> error
based_on_state_digest empty -> error
current_state.json missing or no state_digest -> error
based_on_state_digest != current_state.state_digest -> error
```

最小 warning 条件：

```text
task_packet missing -> warning
task_packet.execution_scope missing -> warning
active_decision_packet missing -> warning
active_decision_packet 不等于 project_state/decision_packet.md -> warning 或 error，由 Codex 审计后决定
```

### 6.2 CLI 行为

新增 subcommand：

```powershell
python -m reverse_agent.project_state lint-decision --state-dir project_state
```

输出要求：

```text
lint-decision: OK
decision_id: ...
decision_status: APPROVED
based_on_state_digest: ...
current_state_digest: ...
execution_scope: decision_packet_controls_current_round
active_decision_packet: project_state/decision_packet.md
```

失败时：

```text
lint-decision: FAILED
error: decision_meta missing
error: decision status is DRAFT, expected APPROVED
error: based_on_state_digest does not match current_state.state_digest
```

返回码：

```text
0 = OK
1 = lint failed
```

不要让 lint-decision 抛 Python traceback，除非是不可恢复的程序错误。

### 6.3 digest mismatch 说明

本轮 lint 以“当前 live state”为检查对象，所以如果 `decision_meta.based_on_state_digest` 和当前 `current_state.state_digest` 不一致，应当失败。

这与审计历史 round 不冲突：历史 round 应通过 `round_manifest.json` 审计，不通过 live `lint-decision` 判断。

### 6.4 不做 report lint

本轮只做 decision lint，不做完整 report lint。

允许读取 report 但不要把 report 成败纳入 lint-decision 的阻断条件。report 绑定检查已经由上一轮 `decision_report_id_match` 提供。

## 7. Tests

必须新增或修改 `tests/test_project_state.py`，覆盖：

```text
test_lint_decision_ok_for_approved_matching_current_state
test_lint_decision_fails_when_decision_meta_missing
test_lint_decision_fails_when_decision_status_template_only
test_lint_decision_fails_when_decision_status_draft
test_lint_decision_fails_when_decision_id_empty
test_lint_decision_fails_when_based_on_state_digest_empty
test_lint_decision_fails_when_based_on_state_digest_mismatch
test_lint_decision_cli_returns_zero_on_ok
test_lint_decision_cli_returns_nonzero_on_failure
test_lint_decision_reports_execution_scope_and_active_decision_packet
```

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r3
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state
```

注意执行顺序：

```text
如果 build 会刷新 current_state.state_digest，Codex 必须在 build 后确保当前 decision_packet.md 的 decision_meta 仍然指向当前 live state，或者在报告中说明 lint-decision 为什么在 build 前/后预期不同。
最终 pytest_result.txt 必须记录最终可审计状态。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要实现完整 lint framework 或 policy engine。
2. 需要自动改写 decision_packet.md 才能通过测试。
3. 需要读取完整 solve_reports。
4. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
5. 需要推进 samplereverse 逆向任务。
6. lint-decision 会破坏 status/build/archive-round 现有行为。
7. 无法区分 TEMPLATE_ONLY / UNKNOWN / DRAFT / APPROVED。
8. 无法稳定返回非 0 退出码。
9. digest mismatch 规则与现有 build/archive 语义发生不可解释冲突。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. 新增 python -m reverse_agent.project_state lint-decision。
2. APPROVED decision + matching current_state digest 返回 0。
3. missing meta / TEMPLATE_ONLY / DRAFT / 空 decision_id / 空 digest / digest mismatch 返回非 0。
4. lint-decision 输出 readable diagnostics。
5. lint-decision 复用 read_decision_meta()，不重复实现 Markdown parser。
6. status/build/archive-round 原有测试不回退。
7. tests/test_project_state.py 覆盖成功与失败路径。
8. project_state/pytest_result.txt 记录真实测试结果。
9. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
10. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
```

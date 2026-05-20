```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1f_lint_handoff_aggregate_20260520",
  "round_id": "round_20260520_052928",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 1F：实现轻量 `lint-handoff` 聚合门禁，并修正 decision consumed / ready 语义。

本轮仍属于工程架构改造支线，不推进 `samplereverse` 逆向主线，不运行 runtime probe，不进入 Phase 2，不引入重型 workflow runtime。

## 1. Goal

Phase 1D 已有 `lint-decision`，Phase 1E 已有 `lint-report`。现在需要一个轻量聚合命令，帮助 GPT/Codex 在每轮开始或审计前快速判断当前 handoff 状态。

新增命令：

```text
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

本轮目标：

```text
1. 修正 decision_execution_state 的优先级：
   - 如果当前 decision 已有 matching report，则应优先视为 consumed。
   - 不应同时表现为“已经被 report 消费”又“可继续执行”。
2. 新增 decision_ready_for_execution 字段：
   - 只有 APPROVED + state_digest match + 未被 matching report 消费时才为 true。
3. 新增 lint_handoff(state_dir)：
   - 聚合 status_summary / lint_decision / lint_report。
   - 输出当前 handoff_state。
   - 返回 0/1。
4. lint-handoff 不替代 GPT 审计，只做结构化 handoff 健康检查。
5. 不实现完整 workflow engine，不实现 CI，不自动修改 decision/report。
```

建议 handoff_state 最小集合：

```text
READY_FOR_CODEX
REVIEW_COMPLETE
REPORT_NEEDS_REVIEW
STALE_OR_MISMATCH
TEMPLATE_OR_UNKNOWN
FAILED
```

## 2. Current Evidence

当前任务主线：工程架构改造支线。

当前 live state：

```text
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
source_harness_run = sr_lhs_thread_follow_timing_20260520_r4
```

当前 `task_packet.json` 仍显示样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明 `task_packet.task` 不是本轮 Codex 的执行任务；本轮执行权威仍来自 `project_state/decision_packet.md`。

Phase 1E 已完成：

```text
新增 python -m reverse_agent.project_state lint-report。
codex_report_summary.based_on_decision_id 匹配 Phase 1E decision。
tests/test_project_state.py 92 passed。
全量 pytest 345 passed。
lint-report 最终 OK。
round_20260520_phase1e_lint_report 已归档。
```

当前状态中仍有一个语义问题：

```text
decision_consumed_by_report: True
decision_execution_state: READY_FOR_EXECUTION
```

这容易误导后续 Codex 重复执行已经有 SUCCESS report 的 decision。下一轮应把“可执行”和“已消费”明确区分。

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
不要自动修改 decision_packet.md。
不要自动修改 codex_execution_report.md。
不要降低 lint-decision 默认严格性。
不要降低 lint-report 默认结构检查。
不要实现完整 workflow engine、policy engine 或 CI workflow。
不要引入 Temporal / Airflow / Dagster / Argo / LangGraph。
不要引入 PostgreSQL / Redis / Kubernetes。
不要破坏旧 project_state 字段兼容性。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
```

必要时参考：

```text
project_state/rounds/round_20260520_phase1e_lint_report/round_manifest.json
project_state/rounds/round_20260520_phase1e_lint_report/git_diff.patch
docs/phase1_project_state_stability_plan.md
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须在 `codex_execution_report.md` 中说明：

```text
1. 当前 lint-decision 的返回结构和失败条件。
2. 当前 lint-report 的返回结构和 warning/error 条件。
3. 当前 status_summary 中 decision_consumed_by_report 与 decision_execution_state 的关系。
4. 为什么 matching SUCCESS report 应优先把 decision 视为 consumed。
5. 当前 Phase 1E report 是否绑定当前 decision。
6. 当前 round_id 与 current_state.round_id 的 mismatch warning 是否是结构问题还是已知归档策略问题。
7. 如何实现 lint-handoff，而不让它变成完整 workflow engine。
8. 如何保持 lint-decision / lint-report 独立可用。
9. 本轮是否只需要改 project_state.py 与 tests。
10. 是否存在误推进 reverse harness 的风险。
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

### 6.1 修正 decision_execution_state 优先级

调整 `_build_handoff_consistency()` 的判定顺序。

建议规则：

```text
TEMPLATE_OR_UNKNOWN:
  decision_status in TEMPLATE_ONLY/UNKNOWN 或 decision_id 为空。

CONSUMED_BY_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status=SUCCESS。
  不要求 digest stale；只要 matching SUCCESS report 已存在，就说明该 decision 已被成功 report 消费。

CONSUMED_BY_NON_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status in PARTIAL/FAILED/BLOCKED。

READY_FOR_EXECUTION:
  decision_status=APPROVED，decision_state_digest_match=True，且 decision_report_id_match=False。

STALE_WITHOUT_MATCHING_REPORT:
  decision_status=APPROVED，decision_state_digest_match=False，且 decision_report_id_match=False。
```

新增字段：

```text
decision_ready_for_execution: bool
```

规则：

```text
decision_ready_for_execution = decision_execution_state == READY_FOR_EXECUTION
```

`status_summary()` 和 CLI `status` 都应输出该字段。

### 6.2 新增 lint-handoff

建议新增函数：

```text
lint_handoff(state_dir: Path) -> dict[str, Any]
```

返回结构建议：

```json
{
  "ok": true,
  "handoff_state": "REVIEW_COMPLETE",
  "errors": [],
  "warnings": [],
  "decision_execution_state": "CONSUMED_BY_SUCCESS_REPORT",
  "decision_ready_for_execution": false,
  "decision_report_id_match": true,
  "lint_decision_ok": true,
  "lint_report_ok": true,
  "lint_decision_errors": [],
  "lint_report_errors": [],
  "lint_report_warnings": []
}
```

最小判定建议：

```text
READY_FOR_CODEX:
  decision_execution_state=READY_FOR_EXECUTION 且 lint-decision OK。
  返回 0。

REVIEW_COMPLETE:
  decision_execution_state=CONSUMED_BY_SUCCESS_REPORT 且 lint-report OK。
  返回 0。

REPORT_NEEDS_REVIEW:
  decision_execution_state=CONSUMED_BY_NON_SUCCESS_REPORT 且 lint-report 结构 OK。
  返回 0，但输出 warning。

STALE_OR_MISMATCH:
  decision_execution_state=STALE_WITHOUT_MATCHING_REPORT。
  返回 1。

TEMPLATE_OR_UNKNOWN:
  decision_execution_state=TEMPLATE_OR_UNKNOWN。
  返回 1。

FAILED:
  lint-decision 或 lint-report 存在 hard errors，且不能被 consumed-report 语义解释。
  返回 1。
```

注意：

```text
lint-handoff 是聚合诊断，不自动批准代码。
GPT 审计结论仍以 DECISION_PACKET / CODEX_EXECUTION_REPORT / pytest_result / diff 为准。
```

### 6.3 CLI 行为

新增 subcommand：

```powershell
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

输出要求：

```text
lint-handoff: OK / FAILED
handoff_state: ...
decision_execution_state: ...
decision_ready_for_execution: True/False
decision_report_id_match: True/False
lint_decision_ok: True/False
lint_report_ok: True/False
```

如果有 warning/error，逐行输出：

```text
warning: ...
error: ...
```

返回码：

```text
0 = handoff structurally OK
1 = handoff failed or stale/mismatch
```

### 6.4 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase1f_lint_handoff_aggregate_20260520",
  "round_id": "<actual_round_id>",
  "based_on_decision_id": "decision_phase1f_lint_handoff_aggregate_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

## 7. Tests

必须新增或修改 `tests/test_project_state.py`，覆盖：

```text
test_status_summary_consumed_success_takes_priority_over_ready_when_report_matches
test_status_summary_decision_ready_for_execution_requires_no_matching_report
test_status_cli_prints_decision_ready_for_execution
test_lint_handoff_ready_for_codex_when_decision_ready
test_lint_handoff_review_complete_when_success_report_consumed
test_lint_handoff_report_needs_review_for_non_success_report
test_lint_handoff_fails_for_stale_without_matching_report
test_lint_handoff_fails_for_template_or_unknown_decision
test_lint_handoff_cli_returns_zero_on_review_complete
test_lint_handoff_cli_returns_nonzero_on_stale_mismatch
```

保留并确保通过：

```text
lint-decision 现有测试。
lint-report 现有测试。
decision_execution_state 现有测试需要按新优先级更新。
status/build/archive-round 原有行为不回退。
```

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260520_phase1f_lint_handoff
```

如果 `lint-handoff` 在最终 report 写入前失败或返回不同状态，必须在 `pytest_result.txt` 中标注为 expected pre-report state。最终 `pytest_result.txt` 必须记录最终 `lint-handoff` 结果。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
3. 需要自动修改 decision_packet.md 才能完成。
4. 需要降低 lint-decision 或 lint-report 严格性才能完成。
5. 需要实现完整 workflow engine、policy engine 或 CI。
6. 需要读取完整 solve_reports。
7. 无法区分 READY_FOR_EXECUTION 与 CONSUMED_BY_SUCCESS_REPORT。
8. 无法保持旧 status/build/archive-round 测试通过。
9. 无法让 report 绑定当前 decision_id。
10. 无法让 pytest_result.txt 记录本轮真实测试。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. matching SUCCESS report 优先把 decision_execution_state 判为 CONSUMED_BY_SUCCESS_REPORT。
2. 只有未被 matching report 消费的 APPROVED + digest match decision 才是 READY_FOR_EXECUTION。
3. 新增 decision_ready_for_execution 字段。
4. status_summary 和 CLI status 输出 decision_ready_for_execution。
5. 新增 python -m reverse_agent.project_state lint-handoff。
6. lint-handoff 能区分 READY_FOR_CODEX / REVIEW_COMPLETE / REPORT_NEEDS_REVIEW / STALE_OR_MISMATCH / TEMPLATE_OR_UNKNOWN / FAILED。
7. lint-handoff 复用 lint_decision、lint_report、status_summary，不重复实现 Markdown parser。
8. tests/test_project_state.py 覆盖成功、消费、stale、template、CLI 返回码。
9. project_state/pytest_result.txt 记录真实测试和最终 lint-handoff 输出。
10. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
11. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
```

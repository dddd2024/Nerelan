```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1e_lint_report_min_gate_20260520",
  "round_id": "round_20260520_052928",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 1E：实现最小 `lint-report` 门禁。

本轮仍属于工程架构改造支线，不推进 `samplereverse` 逆向主线，不运行 runtime probe，不进入 Phase 2，不引入重型 workflow runtime。

## 1. Goal

在 Phase 1D 已有 `lint-decision` 的基础上，新增最小、可测试、fail-soft 的 report 门禁：

```text
python -m reverse_agent.project_state lint-report --state-dir project_state
```

本轮目标：

```text
1. 校验 codex_execution_report.md 是否存在机器可读 codex_report_summary。
2. 校验 report_id / round_id / based_on_decision_id 非空。
3. 校验 based_on_decision_id 是否匹配当前 decision_meta.decision_id。
4. 校验 report_status 属于 SUCCESS / PARTIAL / FAILED / BLOCKED，而不是 TEMPLATE_ONLY / UNKNOWN。
5. 校验 acceptance_recommendation 属于 ACCEPTED / REWORK_REQUIRED / BLOCKED / NEEDS_REVIEW / UNKNOWN。
6. 校验 tests_ran 和 generated_artifacts 是列表；SUCCESS 报告下 tests_ran 必须非空，pytest_result.txt 必须存在且非空。
7. 输出人类可读诊断；失败返回非 0。
8. 不做完整 policy engine，不自动修改 report，不把 FAILED/BLOCKED 报告伪装成成功。
```

`lint-report` 的语义是“报告是否结构化、可审计、是否绑定当前 decision”，不是“是否接受本轮代码”。是否 ACCEPTED 仍由 GPT 审计判断。

## 2. Current Evidence

当前任务主线：工程架构改造支线。

当前 live state 是：

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

这说明 `task_packet.task` 不是本轮 Codex 的执行任务；本轮执行权威来自 `project_state/decision_packet.md`。

上一轮 Phase 1D-fix rework 已完成：

```text
codex_report_summary.based_on_decision_id 已匹配当前 decision。
status_summary() 已新增 decision_state_digest_match。
status_summary() 已新增 decision_consumed_by_report。
status_summary() 已新增 decision_execution_state。
CLI status 已打印上述字段。
pytest_result.txt 已记录本轮真实测试。
round_20260520_052928 已归档。
```

当前仍缺少 report 侧门禁。现在只有 `lint-decision`，还没有一条命令能在 Codex 完成后检查 report 是否可审计、是否绑定当前 decision、是否记录测试和归档线索。

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
不要自动修改 codex_execution_report.md 来追当前 decision。
不要降低 lint-decision 默认严格性。
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
project_state/rounds/round_20260520_052928/round_manifest.json
project_state/rounds/round_20260520_052928/git_diff.patch
docs/phase1_project_state_stability_plan.md
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须在 `codex_execution_report.md` 中说明：

```text
1. 当前 main() 已有哪些 subcommand。
2. 当前 lint_decision() 如何组织返回值和 CLI 输出。
3. read_codex_report_summary() 对 missing / invalid / TEMPLATE_ONLY / SUCCESS 的行为。
4. build_handoff_status() 当前如何计算 decision_report_id_match。
5. status_summary() 当前如何暴露 report_status / report_id / report_based_on_decision_id。
6. 当前 codex_report_summary 是否包含 files_changed / tests_ran / generated_artifacts。
7. pytest_result.txt 是否存在、是否非空。
8. round_manifest 是否存在，是否归档 codex_execution_report.md / pytest_result.txt。
9. 如何确保 lint-report 不重复实现 Markdown parser，而是复用 read_codex_report_summary()。
10. 如何只实现 report 最小门禁，不做完整 policy engine。
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

### 6.1 lint-report 行为

建议新增函数：

```text
lint_report(state_dir: Path) -> dict[str, Any]
```

返回结构建议：

```json
{
  "ok": true,
  "errors": [],
  "warnings": [],
  "report_id": "...",
  "report_status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "based_on_decision_id": "...",
  "decision_id": "...",
  "decision_report_id_match": true,
  "round_id": "...",
  "current_state_round_id": "...",
  "tests_ran_count": 3,
  "generated_artifacts_count": 5,
  "pytest_result_present": true
}
```

最小 error 条件：

```text
codex_report_summary missing -> error
report_status in TEMPLATE_ONLY / UNKNOWN -> error
report_id empty -> error
round_id empty -> error
based_on_decision_id empty -> error
current decision_id empty -> error
based_on_decision_id != current decision_id -> error
status=SUCCESS 且 tests_ran 为空 -> error
status=SUCCESS 且 pytest_result.txt 缺失或为空 -> error
files_changed / tests_ran / generated_artifacts 字段存在但不是列表 -> error
```

最小 warning 条件：

```text
round_id 与 current_state.round_id 不一致 -> warning
acceptance_recommendation 为 UNKNOWN -> warning
status 非 SUCCESS 但结构可解析 -> warning
round_manifest 缺失 -> warning
round_manifest 未归档 pytest_result.txt 或 codex_execution_report.md -> warning
```

注意：`PARTIAL / FAILED / BLOCKED` 可以是结构化、可审计的报告；lint-report 不应把它们直接伪装为 ACCEPTED，只输出 report_status 与 warning。

### 6.2 CLI 行为

新增 subcommand：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
```

输出要求：

```text
lint-report: OK / FAILED
report_id: ...
report_status: ...
acceptance_recommendation: ...
based_on_decision_id: ...
decision_id: ...
decision_report_id_match: True/False
round_id: ...
current_state_round_id: ...
tests_ran_count: ...
generated_artifacts_count: ...
pytest_result_present: True/False
```

返回码：

```text
0 = report lint OK
1 = report lint failed
```

不要让 lint-report 抛 Python traceback，除非是不可恢复的程序错误。

### 6.3 与 status_summary 的关系

`lint-report` 可以复用 `build_handoff_status()` / `status_summary()` 的字段，但不要让 `status` 依赖 `lint-report` 才能运行。`status` 仍应是只读、宽容、可显示当前状态的命令。

### 6.4 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase1e_lint_report_min_gate_20260520",
  "round_id": "<actual_round_id>",
  "based_on_decision_id": "decision_phase1e_lint_report_min_gate_20260520",
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
test_lint_report_ok_for_matching_success_report
test_lint_report_fails_when_report_summary_missing
test_lint_report_fails_when_report_status_template_only
test_lint_report_fails_when_report_id_empty
test_lint_report_fails_when_based_on_decision_id_empty
test_lint_report_fails_when_based_on_decision_id_mismatch
test_lint_report_fails_when_success_report_has_empty_tests_ran
test_lint_report_warns_when_round_id_mismatches_current_state
test_lint_report_cli_returns_zero_on_ok
test_lint_report_cli_returns_nonzero_on_failure
```

保留上一轮测试：

```text
lint-decision 成功路径仍返回 0。
lint-decision digest mismatch 仍返回 1。
decision_execution_state 相关测试仍通过。
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
python -m reverse_agent.project_state archive-round --state-dir project_state
```

如果 `lint-report` 在写入最终 report 前失败，必须在 `pytest_result.txt` 中标注为 expected pre-report mismatch；最终 `pytest_result.txt` 必须记录最终 `lint-report` 结果。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
3. 需要自动修改 decision_packet.md 才能完成。
4. 需要降低 lint-decision 严格性才能完成。
5. 需要实现完整 workflow engine、policy engine 或 CI。
6. 需要读取完整 solve_reports。
7. 无法让 report 绑定当前 decision_id。
8. 无法让 pytest_result.txt 记录本轮真实测试。
9. 无法保持旧 status/build/archive-round 测试通过。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. 新增 python -m reverse_agent.project_state lint-report。
2. report summary missing / TEMPLATE_ONLY / UNKNOWN 返回非 0。
3. report_id 空、round_id 空、based_on_decision_id 空返回非 0。
4. based_on_decision_id 与当前 decision_id 不匹配返回非 0。
5. SUCCESS 报告下 tests_ran 为空或 pytest_result.txt 缺失/为空返回非 0。
6. lint-report 输出 readable diagnostics。
7. lint-report 复用 read_codex_report_summary()，不重复实现 Markdown parser。
8. tests/test_project_state.py 覆盖成功与失败路径。
9. project_state/pytest_result.txt 记录真实测试结果与最终 lint-report 结果。
10. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
11. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
```

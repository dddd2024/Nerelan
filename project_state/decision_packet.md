```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1d_fix_rework_handoff_consistency_20260520",
  "round_id": "round_20260520_052928",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮是 Phase 1D-fix rework：恢复 decision/report/state 一致性，并完成上一轮未完成的 decision execution state 语义字段。

本轮仍属于工程架构改造支线，不推进 `samplereverse` 逆向主线，不运行 runtime probe，不进入 Phase 2，不引入重型 workflow runtime。

## 1. Goal

完成上一轮未完成的 Phase 1D-fix，并先恢复 handoff 一致性。

必须完成：

```text
1. codex_execution_report.md 顶部 codex_report_summary 必须绑定当前 decision_id：
   decision_phase1d_fix_rework_handoff_consistency_20260520
2. pytest_result.txt 必须记录本轮真实测试，而不是沿用 Phase 1D 的旧记录。
3. status_summary() 必须新增并返回：
   - decision_state_digest_match
   - decision_consumed_by_report
   - decision_execution_state
4. CLI status 必须打印上述字段。
5. 不推进逆向主线，不运行 runtime probe。
```

允许的最小 `decision_execution_state` 值：

```text
READY_FOR_EXECUTION
CONSUMED_BY_SUCCESS_REPORT
CONSUMED_BY_NON_SUCCESS_REPORT
STALE_WITHOUT_MATCHING_REPORT
TEMPLATE_OR_UNKNOWN
```

本轮不是继续扩展 lint framework，也不是推进 samplereverse；目标是修复当前 handoff 链路，使审计能区分“可执行 decision”“已被 report 消费的 decision”“真正 stale/mismatch decision”。

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

当前上一份 `codex_execution_report.md` 仍绑定旧 decision：

```text
report_id = report_phase1d_lint_decision_min_gate_20260519
report_based_on_decision_id = decision_phase1d_lint_decision_min_gate_20260519
```

这与上一份 Phase 1D-fix decision：

```text
decision_phase1d_fix_lint_phase_semantics_20260519
```

以及当前 rework decision：

```text
decision_phase1d_fix_rework_handoff_consistency_20260520
```

均不匹配。上一轮未生成 Phase 1D-fix 对应报告，也未更新 `pytest_result.txt` 为 Phase 1D-fix 测试记录。

当前 `reverse_agent/project_state.py` 仍只实现了上一轮 `lint_decision()` 和 `decision_report_id_match`，未实现：

```text
decision_state_digest_match
decision_consumed_by_report
decision_execution_state
```

当前 project_state 已混入新的 reverse harness run 引用 `sr_lhs_thread_follow_timing_20260520_r4`。本轮不得继续推进该逆向方向；只允许修复 project_state 工程支线 handoff 一致性。

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
不要自动把任务改成逆向主线。
不要自动修改 decision_packet.md 来追 build 后的新 digest。
不要降低 lint-decision 默认严格性。
不要实现完整 workflow engine 或 policy engine。
不要实现 GitHub Actions / CI workflow。
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
project_state/rounds/round_20260519_105608/round_manifest.json
project_state/rounds/round_20260519_105608/git_diff.patch
docs/phase1_project_state_stability_plan.md
```

如果 `round_20260520_052928` 归档缺失，必须在报告中明确说明，并通过本轮 archive-round 重新建立可信归档。

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须在 `codex_execution_report.md` 中说明：

```text
1. 当前 decision_id 是什么。
2. 当前 report_based_on_decision_id 是否匹配当前 decision_id。
3. 当前 state_digest 是什么。
4. 上一轮为何没有生成 Phase 1D-fix 报告。
5. 当前 project_state 是否混入 reverse harness run，是否存在支线混杂风险。
6. lint_decision() 当前如何判断 digest match。
7. status_summary() 当前已暴露哪些 decision/report 字段。
8. build_handoff_status() 当前如何计算 decision_report_id_match。
9. 本轮如何只改 project_state 工程逻辑，不推进逆向主线。
10. 本轮如何记录 final pytest_result 和 archive-round 状态。
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

### 6.1 status_summary 增强

在 `status_summary()` 或 `build_handoff_status()` 中增加最小字段：

```json
{
  "decision_state_digest_match": true,
  "decision_consumed_by_report": false,
  "decision_execution_state": "READY_FOR_EXECUTION"
}
```

判定规则：

```text
READY_FOR_EXECUTION:
  decision_status=APPROVED，decision_id 非空，decision based_on_state_digest == current_state.state_digest。

CONSUMED_BY_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status=SUCCESS，且 decision based_on_state_digest != current_state.state_digest。

CONSUMED_BY_NON_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status in PARTIAL/FAILED/BLOCKED，且 decision based_on_state_digest != current_state.state_digest。

STALE_WITHOUT_MATCHING_REPORT:
  decision_status=APPROVED，但 digest mismatch 且 report 未绑定该 decision。

TEMPLATE_OR_UNKNOWN:
  decision_status in TEMPLATE_ONLY/UNKNOWN 或 decision_id 为空。
```

不要改变 `lint_decision()` 的默认失败规则。`lint-decision` 仍是 pre-execution gate。

### 6.2 CLI status 输出

`python -m reverse_agent.project_state status --state-dir project_state` 必须额外输出：

```text
decision_state_digest_match: True/False
decision_consumed_by_report: True/False
decision_execution_state: READY_FOR_EXECUTION / CONSUMED_BY_SUCCESS_REPORT / CONSUMED_BY_NON_SUCCESS_REPORT / STALE_WITHOUT_MATCHING_REPORT / TEMPLATE_OR_UNKNOWN
```

### 6.3 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase1d_fix_rework_handoff_consistency_20260520",
  "round_id": "<actual_round_id>",
  "based_on_decision_id": "decision_phase1d_fix_rework_handoff_consistency_20260520",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

### 6.4 pytest_result 记录要求

本轮 `pytest_result.txt` 必须记录：

```text
1. 本轮测试标题必须是 Phase 1D-fix rework handoff consistency。
2. pre-build lint-decision OK 或说明为什么不是 OK。
3. post-build lint-decision 如失败，必须标注为 expected stale。
4. final status 必须输出 decision_execution_state。
5. 如果 final status 是 CONSUMED_BY_SUCCESS_REPORT，则说明本轮 report 已消费当前 decision。
6. archive-round 的执行结果必须记录。
```

## 7. Tests

必须新增或修改 `tests/test_project_state.py`，覆盖：

```text
test_status_summary_decision_ready_for_execution_when_digest_matches
test_status_summary_decision_consumed_by_success_report_when_digest_stale_but_report_matches
test_status_summary_decision_consumed_by_non_success_report_when_digest_stale_but_report_matches
test_status_summary_decision_stale_without_matching_report_when_digest_stale_and_report_differs
test_status_summary_decision_template_or_unknown_for_template_decision
test_status_cli_prints_decision_execution_state
```

保留上一轮测试：

```text
lint-decision 成功路径仍返回 0。
lint-decision digest mismatch 仍返回 1。
status/build/archive-round 原有行为不回退。
```

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state
```

如果 Codex 认为必须重新 build project_state 才能完成归档，允许运行：

```powershell
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_thread_follow_timing_20260520_r4
```

但不得运行任何新的 reverse runtime probe，也不得新增 solve_reports 内容。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要运行逆向 runtime probe。
2. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
3. 无法让 report 绑定当前 decision_id。
4. 无法让 pytest_result.txt 记录本轮测试。
5. 无法实现 decision_execution_state 而不降低 lint-decision 严格性。
6. 需要自动改写 decision_packet.md 来追 build 后的新 digest。
7. 需要实现完整 workflow engine 或 policy engine。
8. 需要读取完整 solve_reports。
9. current state / report / decision 三者无法解释一致性。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary.based_on_decision_id 指向本轮 decision_id。
2. pytest_result.txt 是本轮 Phase 1D-fix rework 的真实测试记录。
3. status_summary 新增 decision_state_digest_match。
4. status_summary 新增 decision_consumed_by_report。
5. status_summary 新增 decision_execution_state。
6. status CLI 打印上述字段。
7. digest match 时状态为 READY_FOR_EXECUTION。
8. digest stale 但 report 绑定且 SUCCESS 时状态为 CONSUMED_BY_SUCCESS_REPORT。
9. digest stale 且 report 不绑定时状态为 STALE_WITHOUT_MATCHING_REPORT。
10. TEMPLATE_ONLY/UNKNOWN decision 状态为 TEMPLATE_OR_UNKNOWN。
11. tests/test_project_state.py 覆盖上述状态。
12. lint-decision 默认严格性保持不变。
13. project_state/rounds/<new_round_id>/round_manifest.json 归档本轮最终状态。
14. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
```

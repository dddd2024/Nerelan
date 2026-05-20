```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1d_fix_lint_phase_semantics_20260519",
  "round_id": "round_20260519_105608",
  "based_on_state_build_id": "state_20260519_105608_74887f4fae41",
  "based_on_state_digest": "74887f4fae41ecbb00daa28525fd79aa2e667e9946145d96dd5fe79de04498c0",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 1D-fix：明确 `lint-decision` 的 pre-execution / post-execution 语义，并补齐最终状态记录。

本轮仍属于工程架构改造支线，不推进 `samplereverse` 逆向主线，不运行 runtime probe，不进入 Phase 2，不引入重型 workflow runtime。

## 1. Goal

上一轮 Phase 1D 已实现最小 `lint-decision` 门禁，但暴露了一个流程语义问题：

```text
Codex 执行前，decision_meta.based_on_state_digest 与 current_state.state_digest 匹配，lint-decision 返回 OK。
Codex 执行 build 后，current_state.state_digest 会更新。
此时同一份 decision_packet.md 仍绑定执行前 state_digest，lint-decision 返回 digest mismatch。
```

这不是代码失败，而是 pre-execution decision 在执行后自然变成 consumed / stale。当前问题是：status / pytest_result / report 没有把这个语义表达清楚，容易让审计误判为失败。

本轮目标是小步修复该协作语义：

```text
1. 保持 lint-decision 严格：默认仍检查 decision_meta.based_on_state_digest == current_state.state_digest。
2. 增加 status_summary 可审计字段，用于区分：
   - decision matches current live state，可作为下一轮执行入口；
   - decision 已被本轮 report 消费，post-build 后 digest stale，这是执行后的正常状态；
   - decision/report 不匹配，是真正的 handoff mismatch。
3. 让 CLI status 输出该 decision freshness / consumption 状态。
4. 让 pytest_result.txt 明确记录：pre-build lint OK、post-build lint expected stale、final status 中 report 已绑定当前 decision。
5. 不自动修改 decision_packet.md，不实现完整 workflow engine。
```

建议新增或复用字段：

```json
{
  "decision_state_digest_match": false,
  "decision_execution_state": "CONSUMED_BY_SUCCESS_REPORT",
  "decision_consumed_by_report": true
}
```

允许的最小 `decision_execution_state` 值：

```text
READY_FOR_EXECUTION
CONSUMED_BY_SUCCESS_REPORT
CONSUMED_BY_NON_SUCCESS_REPORT
STALE_WITHOUT_MATCHING_REPORT
TEMPLATE_OR_UNKNOWN
```

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

当前 live state 身份：

```text
round_id = round_20260519_105608
state_build_id = state_20260519_105608_74887f4fae41
state_digest = 74887f4fae41ecbb00daa28525fd79aa2e667e9946145d96dd5fe79de04498c0
source_harness_run = sr_lhs_last_writer_health_fix_20260518_r3
```

上一轮 Phase 1D 已完成：

```text
新增 python -m reverse_agent.project_state lint-decision。
APPROVED + matching state digest 返回 0。
missing meta / TEMPLATE_ONLY / DRAFT / empty id / empty digest / digest mismatch 返回非 0。
tests/test_project_state.py 71 passed。
全量 pytest 321 passed。
```

上一轮限制：

```text
build 后 current_state.state_digest 更新为 74887f4...
当前 decision_packet.md 仍绑定执行前 digest acd12be...
post-build lint-decision 返回 expected failure。
这说明 decision 被执行后自然 stale，但 status 没有显式区分“已消费”与“错误 mismatch”。
```

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
不要自动修改 decision_packet.md 来追当前 state_digest。
不要把 post-build digest mismatch 简单吞掉。
不要降低 lint-decision 默认严格性。
不要实现完整 lint framework 或 policy engine。
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
project_state/rounds/round_20260519_105608/round_manifest.json
project_state/rounds/round_20260519_105608/git_diff.patch
docs/phase1_project_state_stability_plan.md
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

```text
1. lint_decision() 当前如何判断 digest match。
2. status_summary() 当前已暴露哪些 decision/report 字段。
3. build_handoff_status() 当前如何计算 decision_report_id_match。
4. codex_report_summary.based_on_decision_id 与 decision_id 匹配时，能否说明 decision 已被 report 消费。
5. report_status SUCCESS / PARTIAL / FAILED / BLOCKED 对 execution_state 应如何分类。
6. current_state.state_digest 改变时，为什么不应自动改写 decision_packet.md。
7. pytest_result.txt 当前是否记录了 post-build lint expected failure。
8. archive-round 是否已归档 current_state / decision_packet / report / pytest_result / git_diff。
9. 能否用现有 helper 实现，不重复解析 Markdown，不新增复杂 schema。
10. 本轮是否只需改 project_state.py 与 tests。
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

在 `status_summary()` 或 `build_handoff_status()` 中增加最小字段。

建议字段：

```json
{
  "decision_state_digest_match": true,
  "decision_consumed_by_report": false,
  "decision_execution_state": "READY_FOR_EXECUTION"
}
```

判定建议：

```text
READY_FOR_EXECUTION:
  decision_status=APPROVED，decision based_on_state_digest == current_state.state_digest。

CONSUMED_BY_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status=SUCCESS，且 decision based_on_state_digest != current_state.state_digest。

CONSUMED_BY_NON_SUCCESS_REPORT:
  decision_status=APPROVED，decision_report_id_match=True，report_status in PARTIAL/FAILED/BLOCKED，且 decision based_on_state_digest != current_state.state_digest。

STALE_WITHOUT_MATCHING_REPORT:
  decision_status=APPROVED，但 digest mismatch 且 report 未绑定该 decision。

TEMPLATE_OR_UNKNOWN:
  decision_status in TEMPLATE_ONLY/UNKNOWN 或 decision_id 为空。
```

不要改变 `lint_decision()` 的默认失败规则。lint 仍然是 pre-execution gate。

### 6.2 CLI status 输出

`python -m reverse_agent.project_state status` 应额外输出：

```text
decision_state_digest_match: True/False
decision_consumed_by_report: True/False
decision_execution_state: READY_FOR_EXECUTION / CONSUMED_BY_SUCCESS_REPORT / ...
```

### 6.3 pytest_result 记录要求

本轮 `pytest_result.txt` 必须记录：

```text
1. pre-build lint-decision OK。
2. build 后如果 digest 改变，post-build lint-decision 失败是 expected stale，不是异常。
3. final status 输出 decision_execution_state。
4. 如果 final status 是 CONSUMED_BY_SUCCESS_REPORT，则说明本轮 report 已消费当前 decision。
```

### 6.4 不自动刷新 decision_meta

不要让 Codex 在本轮自动把 `decision_packet.md` 的 `based_on_state_digest` 改成 build 后的新 digest。

原因：

```text
正式 decision 应由 GPT 生成并批准。
Codex 自动刷新 decision_meta 会破坏“GPT 是决策手、Codex 是执行手”的职责边界。
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
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r3
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state
```

如果 post-build lint-decision 失败，必须在 `pytest_result.txt` 里标注为 expected stale，并用 final `status` 的 `decision_execution_state` 说明当前状态。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要修改 lint-decision 默认严格性才能完成。
2. 需要自动改写 decision_packet.md 才能完成。
3. 需要实现完整 workflow engine 或 policy engine。
4. 需要读取完整 solve_reports。
5. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
6. 需要推进 samplereverse 逆向任务。
7. 无法区分 READY_FOR_EXECUTION 与 CONSUMED_BY_SUCCESS_REPORT。
8. 无法保持旧 status/build/archive-round 测试通过。
9. round_manifest 无法归档本轮最终状态。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. lint-decision 默认严格性保持不变。
2. status_summary 新增 decision_state_digest_match。
3. status_summary 新增 decision_consumed_by_report。
4. status_summary 新增 decision_execution_state。
5. status CLI 打印上述字段。
6. digest match 时状态为 READY_FOR_EXECUTION。
7. digest stale 但 report 绑定且 SUCCESS 时状态为 CONSUMED_BY_SUCCESS_REPORT。
8. digest stale 且 report 不绑定时状态为 STALE_WITHOUT_MATCHING_REPORT。
9. TEMPLATE_ONLY/UNKNOWN decision 状态为 TEMPLATE_OR_UNKNOWN。
10. tests/test_project_state.py 覆盖上述状态。
11. project_state/pytest_result.txt 记录真实测试结果与 final status。
12. codex_execution_report.md 顶部 codex_report_summary.based_on_decision_id 指向本轮 decision_id。
13. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
```

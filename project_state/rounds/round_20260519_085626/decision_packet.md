```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase1c_handoff_traceability_fix_20260519",
  "round_id": "round_20260519_071819",
  "based_on_state_build_id": "state_20260519_071819_62dfa8ea2f63",
  "based_on_state_digest": "62dfa8ea2f63f16a89c21eb24ca5da4fd86c3047063dcd8b695e7a25d6fc3ed2",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮进入 Phase 1C-fix：补齐 decision/report 机器可读 handoff 可审计性。

本轮不推进 `samplereverse` 逆向主线，不运行任何 runtime probe，不进入 Phase 1E/1F，不进入 Phase 2，不实现完整 `lint-decision`，不修改逆向策略。

## 1. Goal

修复 Phase 1C 后暴露出的 handoff traceability 缺口：

```text
当前 artifact_index.latest_artifacts_v2 已经可用；
但当前 decision_packet.md 缺少 decision_meta；
当前 codex_execution_report.md 的 based_on_decision_id 为空；
status_summary 显示 decision_status: UNKNOWN；
这导致审查时最多只能 ACCEPTED_WITH_LIMITATIONS。
```

本轮目标是做一个小步、兼容旧状态的修复：

```text
1. 让默认 DECISION_PACKET 模板包含 decision_meta TEMPLATE_ONLY 块。
2. 让默认 CODEX_EXECUTION_REPORT 模板包含 codex_report_summary TEMPLATE_ONLY 块。
3. 在 status_summary/build_handoff_status 中暴露 decision/report 绑定状态。
4. 增加测试覆盖：
   - decision_id 与 based_on_decision_id 匹配；
   - based_on_decision_id 为空或不匹配；
   - 缺失 decision_meta 时不能被误判为 APPROVED；
   - 模板状态为 TEMPLATE_ONLY；
   - selected run 与 other run 同时存在时，非 selected artifact 不能被误标 current。
5. 本轮 Codex 报告必须把 based_on_decision_id 写成：
   decision_phase1c_handoff_traceability_fix_20260519
```

## 2. Current Evidence

当前任务主线：工程架构改造支线。

当前 `task_packet.json` 仍描述样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

这说明 `task_packet.task` 不是本轮 Codex 的执行任务；本轮执行权威来自 `project_state/decision_packet.md`。

当前状态身份：

```text
round_id = round_20260519_071819
state_build_id = state_20260519_071819_62dfa8ea2f63
state_digest = 62dfa8ea2f63f16a89c21eb24ca5da4fd86c3047063dcd8b695e7a25d6fc3ed2
source_harness_run = sr_lhs_last_writer_health_fix_20260518_r3
```

Phase 1C 已经完成 artifact freshness/provenance：

```text
artifact_index.latest_artifacts_v2 已存在。
summary / run_manifest / compare_real_lhs_provenance_audit 等当前 run artifact 标记为 current。
frontier_summary / base64_rc4_static_point_discovery 等 legacy tool_artifacts 标记为 stale。
missing artifact 标记为 missing。
```

当前 handoff 缺口：

```text
decision_status: UNKNOWN
decision_id: 空
report_status: SUCCESS
report_id: report_phase1c_artifact_freshness_20260519
report_based_on_decision_id: 空
```

因此上一轮只能被审查为 ACCEPTED_WITH_LIMITATIONS，而不是完全 ACCEPTED。

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
不要实现完整 lint-decision。
不要进入 Phase 1E、Phase 1F 或 Phase 2。
不要删除旧 latest_artifacts。
不要破坏旧 decision/report 文件的 fail-soft 行为。
不要覆盖已经存在且非 TEMPLATE_ONLY 的正式 decision_packet.md。
```

## 4. Files To Inspect

必须审计：

```text
reverse_agent/project_state.py
tests/test_project_state.py
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/artifact_index.json
project_state/task_packet.json
project_state/current_state.json
```

必要时参考：

```text
docs/phase1_project_state_stability_plan.md
project_state/rounds/round_20260519_071819/round_manifest.json
project_state/rounds/round_20260519_071819/git_diff.patch
```

不要默认读取完整 `solve_reports/`。

## 5. Required Audit

实现前必须先审计并在 `codex_execution_report.md` 中说明：

```text
1. DECISION_PACKET_TEMPLATE 当前是否包含 decision_meta。
2. CODEX_EXECUTION_REPORT_TEMPLATE 当前是否包含 codex_report_summary。
3. ensure_state_layout() 在什么情况下会写入默认模板，是否会覆盖正式 handoff。
4. read_decision_meta() 对 missing / invalid / TEMPLATE_ONLY / APPROVED 的行为。
5. read_codex_report_summary() 对 missing / invalid / TEMPLATE_ONLY / SUCCESS 的行为。
6. build_handoff_status() 和 status_summary() 当前是否能表达 decision/report mismatch。
7. 当前 codex_execution_report.md 的 based_on_decision_id 为什么为空。
8. Phase 1C 的 latest_artifacts_v2 是否已经正确保留旧 latest_artifacts。
9. 是否已有测试覆盖 decision/report id 匹配与不匹配。
10. 是否已有测试覆盖 selected run 与 other run 同时存在时的 freshness 判定。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
docs/phase1_project_state_stability_plan.md
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

只读或谨慎处理：

```text
project_state/decision_packet.md
```

Codex 不应删除或重写本文件顶部的 `decision_meta`。如果需要在归档中保存当前 decision，只能通过 `archive-round` 完成。

### 6.1 模板修复

在 `reverse_agent/project_state.py` 中更新默认模板：

```text
DECISION_PACKET_TEMPLATE 应包含 decision_meta fenced JSON block。
默认 status 应为 TEMPLATE_ONLY。
默认 decision_id / round_id / based_on_state_build_id / based_on_state_digest 可为空。
```

```text
CODEX_EXECUTION_REPORT_TEMPLATE 应包含 codex_report_summary fenced JSON block。
默认 status 应为 TEMPLATE_ONLY。
默认 acceptance_recommendation 应为 UNKNOWN。
```

必须保持兼容：

```text
旧的非模板 Markdown 缺少 meta 时，仍应解析为 UNKNOWN。
模板文件应解析为 TEMPLATE_ONLY。
正式 decision_packet.md 中 status=APPROVED 时，不能被 ensure_state_layout 覆盖。
```

### 6.2 status_summary 增强

在 `build_handoff_status()` 或 `status_summary()` 中增加最小 handoff 绑定信息。

建议字段：

```json
{
  "handoff_consistency": {
    "decision_report_id_match": true,
    "decision_report_round_match": true,
    "has_approved_decision": true,
    "has_success_report": true,
    "status": "OK"
  }
}
```

允许的最小 status：

```text
OK
MISSING_DECISION_META
MISSING_REPORT_SUMMARY
DECISION_NOT_APPROVED
REPORT_NOT_SUCCESS
DECISION_REPORT_MISMATCH
ROUND_MISMATCH
UNKNOWN
```

不要在本轮实现完整 `lint-decision` CLI。只做 status_summary 可审计字段。

### 6.3 report 绑定要求

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase1c_handoff_traceability_fix_20260519",
  "round_id": "<actual_round_id>",
  "based_on_decision_id": "decision_phase1c_handoff_traceability_fix_20260519",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

### 6.4 selected run freshness 回归测试

补一个更强的 freshness 测试：

```text
构造 selected_run 与 other_run。
两个 run 下存在同类 artifact。
显式 --run-name selected_run。
确认 latest_harness_run 是 selected_run。
确认 latest_artifacts_v2 中被选中的 artifact source_run=selected_run 且 freshness=current。
确认 other_run 的 artifact 不会被误标 current 或覆盖 selected_run。
```

不要为了这个测试读取真实 solve_reports；使用 tmp_path fixture 构造。

## 7. Tests

必须新增或修改 `tests/test_project_state.py`，覆盖：

```text
test_decision_packet_template_contains_template_only_decision_meta
test_codex_report_template_contains_template_only_summary
test_status_summary_handoff_consistency_ok_when_decision_and_report_match
test_status_summary_handoff_consistency_mismatch_when_report_decision_id_empty
test_status_summary_handoff_consistency_mismatch_when_report_decision_id_differs
test_missing_decision_meta_remains_unknown_not_approved
test_selected_run_artifact_wins_over_other_run_for_freshness_current
```

必须运行并记录输出：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
python -m pytest -q
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_lhs_last_writer_health_fix_20260518_r3
python -m reverse_agent.project_state status
python -m reverse_agent.project_state archive-round
```

测试输出写入：

```text
project_state/pytest_result.txt
```

`python -m reverse_agent.project_state status` 的输出至少应能看到：

```text
decision_status: APPROVED
report_status: SUCCESS
report_based_on_decision_id: decision_phase1c_handoff_traceability_fix_20260519
handoff_consistency 或等价字段显示 OK / match true
```

如果 status 在写入最终 report 之前运行，允许先显示非 OK；但最终 `pytest_result.txt` 必须记录最终状态或解释顺序。

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要实现完整 lint-decision 才能完成。
2. 需要大规模重构 project_state.py。
3. ensure_state_layout() 会覆盖正式 decision_packet.md。
4. 模板 meta 会破坏旧测试或旧消费者。
5. 无法区分 TEMPLATE_ONLY 与 UNKNOWN。
6. 无法稳定判断 based_on_decision_id mismatch。
7. 需要读取完整 solve_reports 才能完成测试。
8. 需要修改 reverse strategy、harness 主流程或 olly_scripts。
9. 需要推进 samplereverse 逆向任务。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. 默认 DECISION_PACKET_TEMPLATE 含 decision_meta TEMPLATE_ONLY。
2. 默认 CODEX_EXECUTION_REPORT_TEMPLATE 含 codex_report_summary TEMPLATE_ONLY。
3. 缺失 meta 的旧文件仍安全降级为 UNKNOWN。
4. APPROVED decision + matching SUCCESS report 能在 status_summary 中显示 match / OK。
5. report based_on_decision_id 为空或不匹配时，status_summary 能显式暴露 mismatch。
6. selected_run 与 other_run 同时存在时，非 selected artifact 不会被误标 current。
7. 不修改逆向策略、不运行 runtime probe、不进入 Phase 2。
8. tests/test_project_state.py 覆盖上述行为。
9. project_state/pytest_result.txt 记录真实测试结果。
10. codex_execution_report.md 的 based_on_decision_id 指向当前 decision_id。
```

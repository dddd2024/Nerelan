```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_phase2_completion_audit_fix_review_matrix_20260521",
  "round_id": "round_20260521_phase2_completion_audit_fix_review_matrix",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮是 Phase 2 Completion Audit 的返工修正轮：修正 `docs/phase2_harness_reproducibility_completion.md` 中 Acceptance Matrix 的事实错误。

本轮仍属于工程架构改造支线。不要推进 `samplereverse` 逆向解题，不运行 runtime probe，不新增 Phase 2 子阶段，不改 harness 功能代码，不修改 GPT/Codex 协作协议。

## 1. Goal

修正 Phase 2 completion report 中 Acceptance Matrix 的事实错误。

当前 `docs/phase2_harness_reproducibility_completion.md` 把 Phase 2A-D 的 `GPT review result` 写成 `ACCEPTED`，但 GPT 实际审查结论为：

```text
Phase 2A = ACCEPTED_WITH_LIMITATIONS
Phase 2B = ACCEPTED_WITH_LIMITATIONS
Phase 2C = ACCEPTED_WITH_LIMITATIONS
Phase 2D = ACCEPTED_WITH_LIMITATIONS
```

本轮目标：

```text
1. 修正 docs/phase2_harness_reproducibility_completion.md 的 Acceptance Matrix。
2. 不再把 GPT review result 错写为 ACCEPTED。
3. 如果需要保留 ACCEPTED，应明确它是 Codex acceptance_recommendation，而不是 GPT review result。
4. 保留 No Phase 2E 的结论。
5. 保留 Known Limitations 和 Phase 3 backlog。
6. 只更新文档和 handoff 文件，不改任何功能代码。
```

推荐修正方式：

```text
在 Acceptance Matrix 中拆成两列：
- Codex acceptance_recommendation = ACCEPTED
- GPT review result = ACCEPTED_WITH_LIMITATIONS
```

这样既保留 Codex report 的机器建议，又准确记录 GPT 审查结论。

## 2. Current Evidence

当前执行权威来自 `project_state/decision_packet.md`，不是 `task_packet.task`。

当前 `task_packet.json` 仍显示样本派生任务：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

上轮 Phase 2 Completion Audit report 已绑定：

```text
report_id = report_phase2_completion_audit_20260520
based_on_decision_id = decision_phase2_completion_audit_20260520
status = SUCCESS
acceptance_recommendation = ACCEPTED
```

但 completion 文档中的 Acceptance Matrix 不准确：

```text
Phase 2A GPT review result = ACCEPTED
Phase 2B GPT review result = ACCEPTED
Phase 2C GPT review result = ACCEPTED
Phase 2D GPT review result = ACCEPTED
```

实际 GPT 审查结论应为：

```text
Phase 2A = ACCEPTED_WITH_LIMITATIONS
Phase 2B = ACCEPTED_WITH_LIMITATIONS
Phase 2C = ACCEPTED_WITH_LIMITATIONS
Phase 2D = ACCEPTED_WITH_LIMITATIONS
```

对应限制应继续体现在 Known Limitations / Phase 3 Backlog 中，包括：

```text
1. compare 对不存在 run 可能静默输出空比较。
2. artifact_manifest path 解析仍受 cwd/reports_dir 影响。
3. round_manifest.source_git_commit 仍不是本轮工程提交。
4. archive diff 对新增文件可回放性仍需加强。
```

本轮不是 Phase 2E。Phase 2 的正式范围仍只有 A-D。

## 3. Do Not Do

不要做以下事情：

```text
不要修改 reverse_agent/harness.py。
不要修改 reverse_agent/project_state.py。
不要修改 reverse_agent/strategies/compare_aware_search.py。
不要修改 reverse_agent/olly_scripts/*。
不要修改 reverse_agent/pipeline.py。
不要修改 reverse_agent/tool_runners.py。
不要修改 tests/*。
不要运行逆向 runtime probe。
不要运行 Base64/RC4 breakpoint probe。
不要运行 pipeline 或模型调用。
不要推进 samplereverse 解题。
不要读取或提交完整 solve_reports。
不要新增 Phase 2E。
不要新增 Phase 2 子阶段。
不要修改 GPT/Codex 协作协议。
不要修改 decision_meta / codex_report_summary schema。
不要修改 lint-decision / lint-report / lint-handoff 语义。
不要实现 compare strict。
不要重构 artifact_manifest path schema。
不要修改 round_manifest commit 语义。
不要修改 archive-round / git_diff 行为。
```

## 4. Files To Inspect

必须检查：

```text
docs/phase2_harness_reproducibility_completion.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/decision_packet.md
project_state/rounds/round_20260520_phase2_completion_audit/codex_execution_report.md
project_state/rounds/round_20260520_phase2_completion_audit/pytest_result.txt
```

可选检查：

```text
project_state/rounds/round_20260520_phase2a_harness_resume_policy/codex_execution_report.md
project_state/rounds/round_20260520_phase2b_case_artifact_manifest/codex_execution_report.md
project_state/rounds/round_20260520_phase2c_harness_compare/codex_execution_report.md
project_state/rounds/round_20260520_phase2d_harness_resource_budget/codex_execution_report.md
```

不要默认读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

Codex 必须在 report 中说明：

```text
1. Acceptance Matrix 当前是否把 GPT review result 错写为 ACCEPTED。
2. 是否已将 GPT review result 修正为 ACCEPTED_WITH_LIMITATIONS。
3. 是否新增或保留 Codex acceptance_recommendation = ACCEPTED 的独立列。
4. Known Limitations 和 Phase 3 Backlog 是否仍保留。
5. No Phase 2E 是否仍明确保留。
6. 本轮是否只修正文档和 handoff 文件。
7. 是否没有改功能代码、没有运行 runtime probe、没有运行 pipeline。
```

## 6. Implementation Scope

允许修改：

```text
docs/phase2_harness_reproducibility_completion.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

允许归档：

```text
project_state/rounds/round_20260521_phase2_completion_audit_fix_review_matrix/*
```

禁止修改：

```text
reverse_agent/*
tests/*
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/schema.md
```

如果 Codex 发现必须修改功能代码才能完成，应停止并报告。

### 6.1 Completion report required edit

`docs/phase2_harness_reproducibility_completion.md` 的 Acceptance Matrix 至少应表达：

```text
Phase 2A: Codex acceptance_recommendation = ACCEPTED; GPT review result = ACCEPTED_WITH_LIMITATIONS
Phase 2B: Codex acceptance_recommendation = ACCEPTED; GPT review result = ACCEPTED_WITH_LIMITATIONS
Phase 2C: Codex acceptance_recommendation = ACCEPTED; GPT review result = ACCEPTED_WITH_LIMITATIONS
Phase 2D: Codex acceptance_recommendation = ACCEPTED; GPT review result = ACCEPTED_WITH_LIMITATIONS
```

不要把 `ACCEPTED` 单独标成 GPT review result。

### 6.2 Report binding requirement

本轮完成后，`project_state/codex_execution_report.md` 顶部必须包含：

```json
{
  "schema_version": 1,
  "report_id": "report_phase2_completion_audit_fix_review_matrix_20260521",
  "round_id": "round_20260521_phase2_completion_audit_fix_review_matrix",
  "based_on_decision_id": "decision_phase2_completion_audit_fix_review_matrix_20260521",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}
```

`files_changed`、`tests_ran`、`generated_artifacts` 必须填写真实值，不能留空。

## 7. Tests

因为本轮是文档修正，至少运行：

```powershell
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

建议补充运行：

```powershell
python -m pytest -q tests\test_harness_resume.py
python -m pytest -q tests\test_harness_artifact_manifest.py
python -m pytest -q tests\test_harness_compare.py
python -m pytest -q tests\test_harness_resource_budget.py
```

完成 report 写入后，还必须运行：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260521_phase2_completion_audit_fix_review_matrix
```

注意：

```text
在最终 report 写入前，lint-report 可能因为 report.based_on_decision_id 仍指向 Phase 2 completion audit 而失败。
这属于 expected pre-report mismatch，必须在 pytest_result.txt 中标注。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK / REVIEW_COMPLETE。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要修改功能代码。
2. 需要运行 runtime probe。
3. 需要运行 pipeline 或模型调用。
4. 需要读取或提交完整 solve_reports。
5. 无法确认 GPT review result。
6. 无法修正 Acceptance Matrix 而不改变 Phase 2 closure 结论。
7. 无法让 report.based_on_decision_id 绑定当前 decision_id。
8. 无法让 pytest_result.txt 记录本轮真实检查。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. completion report 不再把 GPT review result 错写为 ACCEPTED。
2. Phase 2A-D 的 GPT review result 写为 ACCEPTED_WITH_LIMITATIONS。
3. 如果保留 ACCEPTED，则它被明确标注为 Codex acceptance_recommendation。
4. Known Limitations 与 Phase 3 Backlog 保留。
5. 明确 No Phase 2E。
6. 不改功能代码。
7. 不运行 runtime probe。
8. 不运行 pipeline 或模型调用。
9. lint-report / lint-handoff 通过。
10. report.based_on_decision_id 指向本轮 decision_id。
11. round archive 已生成。
```

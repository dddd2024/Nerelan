```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rework_classifier_report_consistency",
  "round_id": "round_20260531_rework_classifier_report_consistency",
  "based_on_state_build_id": "state_20260531_140637_bec34f75e725",
  "based_on_state_digest": "bec34f75e725e19caacd862d21c6989ae9cc44bd5a89610c6a48ca490a328c28",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮是上一轮 `decision_20260531_bounded_handoff_exit_classifier_probe` 的返工轮。GPT 审计结论为 `REWORK_REQUIRED`：classifier 核心功能已完成，但 `lint-decision` 失败，`pytest_result_summary.status=PARTIAL`，而 `codex_report_summary.status=SUCCESS` / `acceptance_recommendation=ACCEPTED`，三者状态语义不一致。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只能作为状态派生建议，不能覆盖本 decision。

本轮仍属于 **samplereverse 逆向解题主线**，但不是新 runtime 解题轮。本轮只修 `lint-decision` / report / pytest_result / round manifest 状态一致性，不重新运行 handoff classifier，不运行新 probe，不扩大搜索。

## 1. Goal

修复上一轮 classifier probe 的验收阻断问题，使 project_state 状态一致、机器可审计：

```text
1. 解决或正确定义 `lint-decision` 在 classifier artifact/project_state rebuild 后的 digest mismatch 行为。
2. 让 `codex_execution_report.md`、`pytest_result.txt`、lint 结果三者状态一致。
3. 如果仍无法让 `lint-decision` 通过，则不得写 SUCCESS/ACCEPTED，必须降级为 PARTIAL / ACCEPTED_WITH_LIMITATIONS 或 REWORK_REQUIRED。
4. 补齐 `files_changed` / `generated_artifacts`，明确列出 round archive 文件和 `project_state/model_gate.json` 的变更来源。
5. 保留上一轮 classifier 结果，不重新生成 runtime artifact。
```

上一轮 classifier 结果可以保留：

```text
compare_handoff_exit_classifier_audit.json generated
candidate_count=3
runtime_backed_count=3
overall_classification=candidate_dependent_non_reaching_path
```

本轮允许修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/decision_packet.md
project_state/model_gate.json  # 仅当需要同步状态且必须解释
project_state/rounds/round_20260531_bounded_handoff_exit_classifier_probe/*  # 仅补充/修正归档元数据
reverse_agent/project_state.py  # 仅当选择修复 lint-decision 消费后 digest mismatch 语义
相关 tests/test_project_state.py  # 仅当修改 lint 逻辑
```

原则上不应修改 runtime/solver/strategy。若为了 lint 修复只需报告降级，则不要改 Python 源码。

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

当前样本：

```text
samplereverse
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

当前 `task_packet.task` / `derived_task` 已被上一轮 build 更新为：

```text
Classify bounded candidate-dependent handoff exit
```

它仍不是当前执行权威。本轮执行权威是本 `decision_packet.md`。

上一轮已完成的有效结果：

```text
1. 新 artifact `compare_handoff_exit_classifier_audit` 已进入 artifact_index.latest_artifacts_v2，freshness=current。
2. current_state.current_bottleneck.stage=compare_handoff_exit_classifier_audit。
3. current_state.current_bottleneck.reason/blocker=candidate_dependent_non_reaching_path。
4. 3 个固定候选都有 per-candidate classification。
5. 未扩大候选、beam、topN、budget、timeout。
6. 未运行 Base64/RC4 material capture。
7. 未回旧 sample_solver。
```

上一轮阻断证据：

```text
1. pytest_result_summary.status=PARTIAL。
2. lint-decision FAILED。
3. 失败原因为 based_on_state_digest 不匹配 current_state.state_digest。
4. codex_report_summary.status 仍写 SUCCESS。
5. codex_report_summary.acceptance_recommendation 仍写 ACCEPTED。
6. report 与 pytest_result 语义不一致。
```

当前 state build 已更新为：

```text
state_build_id=state_20260531_140637_bec34f75e725
state_digest=bec34f75e725e19caacd862d21c6989ae9cc44bd5a89610c6a48ca490a328c28
```

本 decision 的 `based_on_state_digest` 已使用当前 digest，因此本轮 `lint-decision` 应该能够通过。若不能通过，必须明确报告失败原因。

## 3. Do Not Do

严禁：

```text
1. 不重新运行 compare_handoff_exit_classifier_audit runtime sidecar。
2. 不运行 sample.exe。
3. 不运行 samplereverse harness。
4. 不运行任何新 runtime probe。
5. 不运行 Base64/RC4 breakpoint probe。
6. 不做 Base64/RC4 material capture。
7. 不回旧 sample_solver。
8. 不扩大候选、beam、topN、budget、timeout。
9. 不新增候选池。
10. 不重复 exact2 basin value-pool evaluation。
11. 不重复 H1/H3 fixed boundary contrast set。
12. 不重复 current 5-candidate transform trace consistency audit。
13. 不读取完整 solve_reports/。
14. 不读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不修改 .codex-skills/。
16. 不修改 sample_corpus/reverse/。
17. 不提交完整 solve_reports/。
18. 不新增 rc4enc 静态分析报告。
19. 不把动态事实写入 .codex-skills/。
20. 不把 stale/missing artifact 当 current evidence。
```

本轮重点是状态一致性，不是继续逆向执行。

## 4. Files To Inspect

默认读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
```

必须读取：

```text
project_state/rounds/round_20260531_bounded_handoff_exit_classifier_probe/round_manifest.json
project_state/rounds/round_20260531_bounded_handoff_exit_classifier_probe/codex_execution_report.md
project_state/rounds/round_20260531_bounded_handoff_exit_classifier_probe/pytest_result.txt
project_state/rounds/round_20260531_bounded_handoff_exit_classifier_probe/decision_packet.md
```

只在选择修复 lint 逻辑时读取/修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不得读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
```

不得修改：

```text
.codex-skills/
sample_corpus/reverse/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_handoff_exit_classifier_audit.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/harness.py
reverse_agent/sample_solver.py
```

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. 当前 mainline 是否为 reverse_solving。
2. task_packet.task / derived_task 是否只是派生任务。
3. 本 decision_packet.md 是否控制当前轮。
4. skill_profiles 是否为 reverse-agent-iteration@v2 + samplereverse-frontier@v2。
5. 是否没有重新运行 classifier runtime sidecar。
6. 是否没有运行 sample.exe。
7. 是否没有运行新 runtime probe。
8. 是否没有运行 Base64/RC4 breakpoint probe。
9. 是否没有回旧 sample_solver。
10. 是否没有扩大候选、beam、topN、budget、timeout。
11. 是否保留上一轮 classifier artifact 结果。
12. 上一轮 artifact_index/current_state 是否仍指向 compare_handoff_exit_classifier_audit current。
13. pytest_result_summary.status 是否与实际 checks 一致。
14. codex_report_summary.status 是否与 pytest_result_summary.status 一致。
15. acceptance_recommendation 是否与 lint 结果一致。
16. lint-decision 是否通过。
17. lint-report 是否通过。
18. git diff --check 是否通过。
19. 如果 lint-decision 仍失败，是否把 report 降级而不是写 SUCCESS/ACCEPTED。
20. files_changed 是否列出本轮实际变更。
21. generated_artifacts 是否列出本轮新生成/更新的 round archive 或报告文件。
22. 是否解释 `project_state/model_gate.json` 的变更来源，若发生变更。
23. 是否没有修改 .codex-skills/。
24. 是否没有修改 sample_corpus/reverse/。
25. 是否没有读取完整 solve_reports/。
26. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
27. negative_results 是否未被重复违反。
```

## 6. Implementation Scope

### 6.1 首选方案：只修报告状态一致性

如果当前 rework decision 的 `based_on_state_digest` 与 current_state digest 一致，优先只执行：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果三项都通过：

```text
1. 更新 codex_execution_report.md 为 SUCCESS / ACCEPTED。
2. 更新 pytest_result.txt 为 PASSED。
3. 在 report 中说明上一轮 classifier artifact 未重新运行，仅保留结果。
4. files_changed 只列本轮改动文件。
5. generated_artifacts 只列本轮实际生成/更新的归档或报告文件。
```

### 6.2 如果 lint-decision 仍失败

若 `lint-decision` 仍因 digest mismatch 或 consumed decision 语义失败，不能掩盖失败。必须二选一：

```text
方案 A：修复 reverse_agent.project_state 的 lint-decision 语义
- 仅允许针对“decision 已被 matching report 消费后 current_state digest 更新”的场景做明确、可测试的兼容逻辑。
- 必须新增/更新 tests/test_project_state.py。
- 必须运行完整 tests/test_project_state.py。

方案 B：不改源码，降级 report
- codex_report_summary.status 不得为 SUCCESS。
- acceptance_recommendation 不得为 ACCEPTED。
- pytest_result_summary.status 保持 PARTIAL 或 FAILED。
- 明确给出下一轮最小修复任务。
```

不得出现：

```text
lint-decision FAILED
pytest_result_summary.status=PARTIAL
codex_report_summary.status=SUCCESS
acceptance_recommendation=ACCEPTED
```

### 6.3 Round archive 修正

如果本轮更新了 report/pytest_result，应同步归档当前 rework round，或明确不归档的原因。

上一轮 classifier round archive 已存在时，不要重复覆盖其事实内容；只允许补充状态说明，且必须在 report 中列出。

### 6.4 不实现新 runtime 功能

本轮不得修改上一轮新增 classifier sidecar、Olly script 或 strategy runtime 逻辑。若发现上一轮 classifier 代码有 bug，只记录为后续 decision，不在本轮修。

## 7. Tests

必须运行并记录：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果修改 `reverse_agent/project_state.py` 或 `tests/test_project_state.py`，还必须运行：

```text
python -m pytest -q tests/test_project_state.py
python -m py_compile reverse_agent/project_state.py
```

如果意外修改其他 Python 文件，必须运行对应测试，并在 report 中解释为什么发生修改。

`pytest_result.txt` 顶部必须包含：

```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_20260531_rework_classifier_report_consistency",
  "report_id": "<actual_report_id>",
  "round_id": "round_20260531_rework_classifier_report_consistency",
  "status": "PASSED_or_PARTIAL_or_FAILED",
  "tests_ran": []
}
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 或 `REWORK_REQUIRED` 的条件：

```text
1. 当前 project_state 文件缺失，无法判断 classifier round 状态。
2. `lint-decision` 失败且无法通过本轮允许范围修复。
3. `lint-report` 失败且无法通过只修 report/pytest_result 修复。
4. 必须重新运行 runtime sidecar 才能继续。
5. 必须读取完整 solve_reports/ 才能继续。
6. 必须修改 .codex-skills/ 才能继续。
7. 必须修改 sample_corpus/reverse/ 才能继续。
```

验收标准：

```text
ACCEPTED:
- decision/report/pytest_result ID 对齐。
- lint-decision 通过。
- lint-report 通过。
- git diff --check 通过。
- pytest_result_summary.status 与 codex_report_summary.status 语义一致。
- acceptance_recommendation 与实际 checks 一致。
- 没有重新运行 runtime classifier。
- 没有修改 solver/runtime/strategy/skill/sample_corpus。
- files_changed/generated_artifacts 完整准确。

ACCEPTED_WITH_LIMITATIONS:
- 核心状态一致性完成，但 GitHub 侧仍无法复核 solve_reports artifact 内容。
- 或只采用 report 降级方案，明确保留 classifier 功能结果但不宣称 full ACCEPTED。

REWORK_REQUIRED:
- lint-decision 仍失败但 report 仍写 SUCCESS/ACCEPTED。
- pytest_result 与 codex_report_summary 状态不一致。
- files_changed/generated_artifacts 缺失关键变更。

BLOCKED:
- project_state 缺失或冲突，无法在本轮范围内修复。
```

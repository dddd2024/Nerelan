```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_report_status_consistency_rework",
  "round_id": "round_20260601_report_status_consistency_rework",
  "based_on_state_build_id": "state_20260601_053247_0a1efec62722",
  "based_on_state_digest": "0a1efec627229ad0ce7c502fe51d0b02bfba8ebdaebdc4ea9f2fb11e42a61220",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮是 **samplereverse 逆向解题主线的状态/报告一致性返工轮**，不是继续逆向探针。

上一轮 `decision_20260601_branch_operand_runtime_sidecar_audit` 已经生成 `compare_handoff_branch_operand_runtime_audit`，并把当前 bottleneck 推进到 `instruction_boundary_gap`。但是审计发现上一轮报告和测试记录存在机器可审计性问题：`codex_execution_report.md` 自称 `PARTIAL / NEEDS_REVIEW`，并记录 `lint-decision` 与初始 `lint-report` 失败；`pytest_result.txt` 的 `pytest_result_summary.status` 却写成 `PASSED`。这使当前 project_state 不能被接受。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

本轮只修复 report / pytest / decision / archive 的一致性。不要继续 `hook_surface_repair`，不要新增 runtime sidecar，不能继续逆向搜索。

## 1. Goal

修复当前 project_state 的状态一致性，使以下文件之间可以被机器审计：

```text
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
project_state/task_packet.json
project_state/rounds/<round_id>/round_manifest.json
```

本轮必须完成：

```text
1. 明确上一轮 branch operand audit 的最终状态是 PARTIAL，而不是 PASSED/ACCEPTED。
2. 修正 pytest_result_summary，不能把失败的 lint-decision / lint-report 写成整体 PASSED。
3. 重新运行最终 lint-decision / lint-report / status，并让最终记录与实际结果一致。
4. 若最终 lint 仍失败，codex_report_summary 必须标记 FAILED 或 BLOCKED，不能标记 SUCCESS。
5. 若最终 lint 通过，则本轮 report 可标记 SUCCESS，但必须说明它只修复状态一致性，不推进逆向证据。
6. 归档本轮 rework round。
```

本轮不要求也不允许捕获 branch operand / flags / next basic block。该工作留给下一轮 `hook_surface_repair`，前提是本轮状态一致性先被修复。

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

`.codex-skills/registry.json` 当前只登记两个 active skill：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Repair bounded handoff branch hook surface
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 state：

```text
state_build_id=state_20260601_053247_0a1efec62722
state_digest=0a1efec627229ad0ce7c502fe51d0b02bfba8ebdaebdc4ea9f2fb11e42a61220
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 bottleneck：

```text
stage=compare_handoff_branch_operand_runtime_audit
blocker=instruction_boundary_gap
reason=instruction_boundary_gap
confidence=medium
```

current artifact：

```text
compare_handoff_branch_operand_runtime_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_branch_operand_runtime_audit\compare_handoff_branch_operand_runtime_audit.json
  sha256=22d2e3dabea0b53d60d5a77e71391c3eae5152ddf1fe564ed80ada4ae443b654
```

上一轮有效证据：

```text
root_cause_classification=instruction_boundary_gap
branch_guard_explained=false
return_context_candidate_dependent=true
return_target_trust=suspicious
exception_edge_shared_for_subset=true
exception_edge_candidate_dependent_memory=true
next_bounded_action=hook_surface_repair
```

上一轮问题：

```text
1. codex_report_summary.status=PARTIAL。
2. codex_report_summary.acceptance_recommendation=NEEDS_REVIEW。
3. codex_execution_report.md 明确记录 lint-decision FAILED after rebuild。
4. codex_execution_report.md 明确记录 lint-report initial pre-refresh FAILED。
5. pytest_result_summary.status 却为 PASSED。
6. pytest_result_summary.tests_ran 包含失败 lint 命令，但 summary 没有体现失败。
```

这违反了状态可信记录原则：如果 lint 失败或 report 与 decision 不一致，不能把本轮标记为整体 PASSED。

## 3. Do Not Do

严禁：

```text
1. 不继续 hook_surface_repair。
2. 不新增 runtime sidecar。
3. 不运行样本程序。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不做 Base64/RC4 material capture。
6. 不做 crypto hook、material hook、Base64/RC4 hook。
7. 不新增候选池。
8. 不扩大 beam / topN / budget / timeout。
9. 不回旧 sample_solver 盲搜。
10. 不重复 compare_handoff_branch_operand_runtime_audit 来制造同样 instruction_boundary_gap。
11. 不修改 compare evidence 或伪造 branch operand / flags。
12. 不把 stale/missing artifact 当 current evidence。
13. 不读取完整 solve_reports/。
14. 不读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不修改 .codex-skills/。
16. 不修改 sample_corpus/reverse/。
17. 不修改 reverse_agent/harness.py。
18. 不提交完整 solve_reports/。
19. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许的修改范围只限状态一致性、测试记录、报告记录、必要的 lint/report 机器可读字段修复。若发现 lint 工具本身存在明显 bug，可以最小化修改 `reverse_agent/project_state.py` 和对应测试，但必须在报告中说明。

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
.codex-skills/registry.json
project_state/rounds/round_20260601_branch_operand_runtime_sidecar_audit/round_manifest.json
```

允许检查和修改：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/decision_packet.md
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/model_gate.json
project_state/rounds/round_20260601_report_status_consistency_rework/
```

只有发现 lint/report 校验逻辑存在真实缺陷时，才允许最小化修改：

```text
reverse_agent/project_state.py
tests/test_project_state.py
```

不得修改：

```text
.codex-skills/
sample_corpus/reverse/
reverse_agent/harness.py
reverse_agent/sample_solver.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/
PROJECT_PROGRESS_LOG.txt
rc4enc_static_analysis_report.md
```

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. 当前 mainline 是否为 reverse_solving。
2. task_packet.task / derived_task 是否只是派生任务。
3. 本 decision_packet.md 是否控制当前轮。
4. skill_profiles 是否为 reverse-agent-iteration@v2 + samplereverse-frontier@v2。
5. .codex-skills/registry.json 是否仍只登记这两个 active skills。
6. 是否没有继续 hook_surface_repair。
7. 是否没有新增 runtime sidecar。
8. 是否没有运行样本程序。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有新增候选、扩大 beam/topN/budget/timeout。
12. 是否没有读取完整 solve_reports/。
13. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
14. 是否没有修改 .codex-skills/。
15. 是否保留 compare_handoff_branch_operand_runtime_audit 的 current artifact，不伪造 branch evidence。
16. 是否明确上一轮状态为 PARTIAL / NEEDS_REVIEW。
17. 是否修正 pytest_result_summary 与正文冲突。
18. 是否最终运行 lint-decision。
19. 是否最终运行 lint-report。
20. 是否最终运行 status。
21. pytest_result_summary.status 是否与最终命令真实结果一致。
22. codex_report_summary.status 是否与本轮真实结果一致。
23. codex_report_summary.based_on_decision_id 是否等于 decision_20260601_report_status_consistency_rework。
24. pytest_result_summary.decision_id 是否等于 decision_20260601_report_status_consistency_rework。
25. pytest_result_summary.report_id 是否等于本轮 report_id。
26. pytest_result_summary.round_id 是否等于 round_20260601_report_status_consistency_rework。
27. 若任何最终 lint 失败，是否将本轮标记为 FAILED 或 BLOCKED。
28. 若所有最终 lint 通过，是否将本轮限制为状态一致性修复，不声称推进逆向证据。
29. 是否归档本轮 round。
30. git diff --check 是否通过。
```

## 6. Implementation Scope

### 6.1 修正状态记录

必须修正 `project_state/pytest_result.txt`：

```text
1. 不能再出现 summary=PASSED 但正文记录 lint 失败的冲突。
2. tests_ran 只能列入本轮最终实际运行且结果被正文准确记录的命令。
3. 如果记录失败命令，summary.status 必须是 FAILED 或 BLOCKED，不得为 PASSED。
4. 如果 preliminary failed checks 保留在正文，必须明确它们是历史/诊断记录，不得计入最终 tests_ran 的 PASSED 集合。
```

必须修正 `project_state/codex_execution_report.md`：

```text
1. 顶部 codex_report_summary 必须指向本 decision_id。
2. status 必须真实表达本轮状态一致性修复结果。
3. acceptance_recommendation 必须与 status 匹配。
4. 不得把上一轮 branch audit 的 PARTIAL 结果说成已 ACCEPTED。
5. 必须说明本轮没有推进 branch operand evidence，只修复状态记录。
```

### 6.2 重新校验

在最终 report / pytest_result 写入后，必须运行：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果这些命令中任意一个最终失败：

```text
1. codex_report_summary.status 不得为 SUCCESS。
2. pytest_result_summary.status 不得为 PASSED。
3. 报告必须明确失败命令和阻断原因。
```

### 6.3 是否需要 rebuild

只有在确认 state 文件与 artifact_index 不一致时，才运行：

```text
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
```

如果 rebuild 会改变 state_digest，必须随后确保 `decision_packet.md`、`codex_execution_report.md`、`pytest_result.txt` 的 metadata 与最终状态一致。不得留下 `lint-decision` 失败然后仍写 PASSED。

### 6.4 归档

通过最终校验后，归档本轮：

```text
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260601_report_status_consistency_rework
```

归档后如果再次修改 report 或 pytest_result，必须重新归档或明确旧归档已 stale。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果修改 `reverse_agent/project_state.py` 或 `tests/test_project_state.py`，还必须运行：

```text
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py -k "pytest_result or lint_report or lint_decision or report_status"
```

如果未修改代码，只修改 project_state 文件，不要虚构 pytest 覆盖。

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_report_status_consistency_rework
round_id=round_20260601_report_status_consistency_rework
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与本轮 report 匹配。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. 最终 lint-decision 失败。
2. 最终 lint-report 失败。
3. pytest_result_summary 无法与正文真实命令结果一致。
4. codex_report_summary 无法与当前 decision_id 对齐。
5. 需要继续运行 runtime sidecar 或 hook_surface_repair 才能修复状态记录。
6. 需要修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
7. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=FAILED` 或 `BLOCKED`，并明确最小阻断原因；不得声称 SUCCESS，也不得把 pytest_result_summary 写成 PASSED。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_bounded_handoff_path_divergence_audit",
  "round_id": "round_20260531_bounded_handoff_path_divergence_audit",
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

本轮继续 **samplereverse 逆向解题主线**。上一轮 `decision_20260531_rework_classifier_report_consistency` 已完成状态一致性返工，当前 `lint-decision` / `lint-report` / `git diff --check` 已记录通过，`current_state.current_bottleneck.stage=compare_handoff_exit_classifier_audit`，`blocker/reason=candidate_dependent_non_reaching_path`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

本轮目标不是继续报告修复，也不是求最终 flag。本轮只围绕上一轮 classifier 已确认的 3 个固定候选，做一个有界 handoff path divergence audit，定位候选间第一次控制流分歧点和最小下一步证据目标。

## 1. Goal

新增或生成一个 **bounded handoff path divergence audit**，建议 artifact 名称：

```text
compare_handoff_path_divergence_audit.json
```

核心问题：

```text
同 3 个候选都进入 predecessor_handoff_call 和 handoff_helper_entry，
但两个候选随后 process_exception，另一个候选没有 exception、也没有到达 compare successor / actual compare。
它们第一次产生候选相关差异的位置在哪里？差异是 return address、branch condition、exception target、内存状态，还是 instrumentation gap？
```

本轮必须输出：

```text
1. per-candidate event sequence comparison。
2. cross-candidate first_divergence classification。
3. 对 exception_unwind_before_compare 的两个候选，记录 exception address / memory / previous event / next event。
4. 对 branch_guard_before_compare 的候选，记录 handoff_helper_entry 后未命中 successor/compare/exception 的最小解释。
5. overall classification 是否仍为 candidate_dependent_non_reaching_path。
6. 下一轮最小 action：branch operand provenance、exception edge audit、hook surface correction，或 instrumentation repair。
```

本轮可以优先从已有 current classifier artifact 做离线 divergence projection；只有当已有 artifact 缺少必要字段时，才允许新增一个 bounded runtime sidecar。若新增 runtime sidecar，必须使用同 3 个固定候选，且只围绕 handoff surface 捕获事件，不做 material capture。

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

当前 `task_packet.task` / `derived_task` 为：

```text
Classify bounded candidate-dependent handoff exit
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 state：

```text
state_build_id=state_20260531_140637_bec34f75e725
state_digest=bec34f75e725e19caacd862d21c6989ae9cc44bd5a89610c6a48ca490a328c28
```

当前 bottleneck：

```text
stage=compare_handoff_exit_classifier_audit
blocker=candidate_dependent_non_reaching_path
reason=candidate_dependent_non_reaching_path
confidence=medium
```

current artifact：

```text
compare_handoff_exit_classifier_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_exit_classifier_audit\compare_handoff_exit_classifier_audit.json
```

上一轮 classifier 结果：

```text
candidate_count=3
runtime_backed_count=3
overall_classification=candidate_dependent_non_reaching_path
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141 -> exception_unwind_before_compare
5a3e7f46ddd474d041414141414141 -> exception_unwind_before_compare
78d540b49c59076f41414141414141 -> branch_guard_before_compare
```

已知 event surface：

```text
predecessor_handoff_call
handoff_helper_entry
process_exception
first_compare_successor
actual_compare
```

已知禁止结论：

```text
1. fallback compare args 仍不能当作 provenance。
2. old [ebp-0x1170] 不能复用为 real LHS source。
3. Base64/RC4 breakpoint probe 仍被 negative_results 阻断，直到 real lhs producer 被证明。
```

## 3. Do Not Do

严禁：

```text
1. 不回旧 sample_solver 盲搜。
2. 不扩大 beam / topN / budget / timeout。
3. 不新增候选池。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不做 Base64/RC4 material capture。
6. 不重复 exact2 basin value-pool evaluation。
7. 不重复 H1/H3 fixed boundary contrast set。
8. 不重复 current 5-candidate transform trace consistency audit。
9. 不重复 compare_handoff_exit_classifier_audit 只为得到同样分类。
10. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
11. 不复用旧 [ebp-0x1170] 作为 real LHS source。
12. 不读取完整 solve_reports/。
13. 不读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不修改 .codex-skills/。
15. 不修改 sample_corpus/reverse/。
16. 不提交完整 solve_reports/。
17. 不新增 rc4enc 静态分析报告。
18. 不把 stale/missing artifact 当 current evidence。
```

本轮允许 runtime 的边界：

```text
1. 只有在 current classifier artifact 不足以做 divergence projection 时，才允许新增 bounded runtime sidecar。
2. 必须使用同 3 个固定候选。
3. 只允许 handoff surface：predecessor_handoff_call / handoff_helper_entry / process_exception / first_compare_successor / actual_compare / 必要的 branch/return context。
4. 不允许 candidate search、material hooks、crypto hooks、Base64/RC4 hooks。
```

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

必须有界读取：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/compare_handoff_exit_classifier_audit.json
```

允许有界读取同 artifact 目录下的 3 个 candidate 子结果，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/candidate_1/compare_handoff_exit_classifier_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/candidate_2/compare_handoff_exit_classifier_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/candidate_3/compare_handoff_exit_classifier_audit.json
```

允许检查和修改：

```text
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
reverse_agent/project_state.py
tests/test_project_state.py
project_state/artifact_index.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有需要新增 runtime sidecar 时，才允许新增/修改：

```text
reverse_agent/olly_scripts/compare_handoff_path_divergence_audit.py
```

不得修改：

```text
.codex-skills/
sample_corpus/reverse/
reverse_agent/harness.py
reverse_agent/sample_solver.py
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
5. 是否保持同 3 个固定候选。
6. 是否没有扩大候选、beam、topN、budget、timeout。
7. 是否没有运行 Base64/RC4 breakpoint probe。
8. 是否没有运行 material capture。
9. 是否没有回旧 sample_solver。
10. 是否没有读取完整 solve_reports/。
11. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/。
13. 是否没有修改 sample_corpus/reverse/。
14. 是否没有把 stale/missing artifact 当 current。
15. 是否读取了 current compare_handoff_exit_classifier_audit。
16. 是否输出 compare_handoff_path_divergence_audit 或等价 artifact。
17. artifact 是否包含 per-candidate event sequence。
18. artifact 是否包含 cross-candidate first_divergence。
19. artifact 是否记录两个 exception candidates 的 exception address / memory / previous event。
20. artifact 是否记录 branch_guard candidate 未到达 successor/compare/exception 的原因。
21. artifact 是否给出 next_bounded_action。
22. artifact_index 是否 additive 更新，不删除旧字段。
23. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
24. negative_results 是否未被重复违反。
25. lint-decision 是否通过。
26. lint-report 是否通过。
27. 相关 pytest 是否通过。
28. git diff --check 是否通过。
```

## 6. Implementation Scope

### 6.1 首选：offline divergence projection

先从 current classifier artifact 中提取：

```text
candidate_hex
classification
events
hook_hit_order
process_exception_context
first_compare_successor_observed
actual_compare_observed
process_exception_observed
return_address_module_offset
scripted_hook_status
scripted_returncode
```

生成 `compare_handoff_path_divergence_audit.json`，最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "source_artifact": "compare_handoff_exit_classifier_audit",
  "candidate_count": 3,
  "runtime_backed_count": 3,
  "candidates": [
    {
      "candidate_hex": "...",
      "prior_classification": "exception_unwind_before_compare",
      "event_sequence": ["predecessor_handoff_call", "handoff_helper_entry", "process_exception"],
      "return_address_summary": {},
      "exception_summary": {},
      "first_divergence_role": "exception_path"
    }
  ],
  "cross_candidate": {
    "common_prefix_events": ["predecessor_handoff_call", "handoff_helper_entry"],
    "first_divergence_after": "handoff_helper_entry",
    "divergence_classes": ["exception_unwind_before_compare", "branch_guard_before_compare"],
    "overall_classification": "candidate_dependent_non_reaching_path"
  },
  "next_bounded_action": "..."
}
```

如果 existing artifact 已足够，禁止重新运行 runtime。

### 6.2 仅在必要时新增 bounded runtime sidecar

如果 offline projection 无法回答 first divergence，需要新增 runtime sidecar 时：

```text
artifact kind: compare_handoff_path_divergence_audit
候选数: 3
surface: predecessor_handoff_call / handoff_helper_entry / process_exception / first_compare_successor / actual_compare / branch-or-return context
不得加入 Base64/RC4/material hooks
不得扩大 timeout/budget，除非必须沿用已有 per_probe_timeout
```

sidecar 只允许补充：

```text
1. handoff_helper_entry 后的 branch/return context。
2. exception 前后一条事件。
3. first_compare_successor 是否命中。
4. actual_compare 是否命中。
5. candidate-specific divergence point。
```

### 6.3 分类规则

建议分类：

```text
两个候选 event sequence = predecessor_handoff_call -> handoff_helper_entry -> process_exception
且第三个候选 = predecessor_handoff_call -> handoff_helper_entry -> no successor/no compare/no exception
=> first_divergence_after=handoff_helper_entry
=> overall_classification=candidate_dependent_non_reaching_path
```

更细分：

```text
exception candidates share same exception module_offset/address pattern
=> exception_edge_shared_for_subset

branch candidate has no exception but also no successor/compare
=> branch_guard_or_silent_non_reaching_path

return_address_module_offset differs across candidates before divergence
=> return_context_candidate_dependent

insufficient event data
=> instrumentation_inconclusive
```

### 6.4 Project state update

如果生成 artifact：

```text
artifact_index.latest_artifacts_v2.compare_handoff_path_divergence_audit = current
current_state.latest_compare_handoff_path_divergence_audit = summary
current_state.current_bottleneck.stage = compare_handoff_path_divergence_audit
```

如果 next action 是 branch operand provenance，下一轮应聚焦 branch guard operand，不得搜索扩展。

如果 next action 是 exception edge audit，下一轮应聚焦 exception source / faulting memory provenance，不得 Base64/RC4 probe。

如果 next action 是 instrumentation repair，下一轮应修 hook surface，不得扩大候选。

## 7. Tests

必须运行：

```text
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果只做 offline projection 且不修改 Python 源码，可不跑 full pytest，但必须说明原因，并至少运行：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果新增/修改 Python 文件，必须运行对应 pytest 和 py_compile。

如果实际运行 bounded runtime sidecar，必须在 report 中记录：

```text
1. exact command
2. candidate_count
3. timeout/budget
4. generated artifact path
5. runtime result status
6. proof that no Base64/RC4/material hook was used
```

`pytest_result.txt` 顶部必须包含：

```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_20260531_bounded_handoff_path_divergence_audit",
  "report_id": "<actual_report_id>",
  "round_id": "round_20260531_bounded_handoff_path_divergence_audit",
  "status": "PASSED_or_PARTIAL_or_FAILED_or_BLOCKED",
  "tests_ran": []
}
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 的条件：

```text
1. current compare_handoff_exit_classifier_audit artifact 在 Codex 本地不可读。
2. 无法确认 3 个固定候选。
3. 需要扩大候选、beam、topN、budget、timeout 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 才能继续。
5. 需要 material capture 才能继续。
6. 需要读取完整 solve_reports/ 才能继续。
7. 无法生成 per-candidate divergence summary。
8. lint-decision 或 lint-report 失败且不能通过只修 project_state/report 修复。
```

验收标准：

```text
ACCEPTED:
- decision/report/pytest_result ID 对齐。
- 保持同 3 个固定候选。
- 输出 compare_handoff_path_divergence_audit 或等价 artifact。
- artifact 包含 per-candidate event sequence 和 cross-candidate first_divergence。
- 明确 next_bounded_action。
- 没有搜索扩展，没有 Base64/RC4 probe，没有 material capture，没有旧 sample_solver。
- artifact_index/current_state additive 更新正确。
- lint 和相关测试通过。

ACCEPTED_WITH_LIMITATIONS:
- artifact 由 offline projection 生成，未新增 runtime，但字段足够支撑下一步。
- 或 GitHub 侧无法复核 solve_reports artifact 内容，但 Codex 本地路径、schema、size 已记录。

REWORK_REQUIRED:
- artifact 缺少 per-candidate divergence。
- 未区分 exception subset 与 branch_guard subset。
- report 与 pytest_result 状态不一致。
- 把 stale/missing artifact 当 current。
- 重复 negative_results 已禁止方向。

BLOCKED:
- current classifier artifact 本地不可读。
- 必须重新 build project_state 或重新生成 classifier 才能继续。
```

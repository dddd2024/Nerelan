```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_handoff_edge_operand_provenance_audit",
  "round_id": "round_20260601_handoff_edge_operand_provenance_audit",
  "based_on_state_build_id": "state_20260531_144509_d2e114f45b75",
  "based_on_state_digest": "d2e114f45b75080eadf84cfb6a85235ebc126abea6246dc295fbce5f0b7a9857",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**。上一轮 `decision_20260531_bounded_handoff_path_divergence_audit` 已完成 bounded handoff path divergence projection，并将当前 bottleneck 推进到 `compare_handoff_path_divergence_audit`。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

本轮目标不是求最终 flag，也不是继续重复 divergence projection。本轮只围绕上一轮已经固定的 3 个候选，做一个 **bounded handoff edge / operand provenance audit**，解释 `handoff_helper_entry` 之后候选相关分歧的最小原因：两个 candidate 为什么进入 exception edge，一个 candidate 为什么变成 branch_guard / silent non-reaching path。

## 1. Goal

新增或生成一个有界 artifact，建议 artifact 名称：

```text
compare_handoff_edge_operand_provenance_audit.json
```

核心问题：

```text
上一轮已确认 3 个候选共同到达 predecessor_handoff_call -> handoff_helper_entry，
随后两个候选进入 process_exception，另一个候选没有 exception、没有 compare successor、也没有 actual compare。
本轮必须判断这个 first divergence after handoff_helper_entry 更接近：
1. branch operand / condition candidate-dependent；
2. exception edge candidate-dependent；
3. return target / return context candidate-dependent；
4. hook surface 或 instrumentation gap。
```

本轮必须输出：

```text
1. per-candidate handoff_helper_entry 后的 edge / operand / exception summary。
2. 两个 exception candidates 的 exception address、memory、previous event、candidate-dependent relation。
3. branch_guard candidate 的 no-exception/no-successor/no-compare 最小解释。
4. cross-candidate root-cause classification。
5. 是否存在可直接进入下一轮的 branch operand provenance、exception edge audit、return context audit、或 hook surface correction。
6. 明确 breakpoint_probe_allowed 仍为 false，除非本轮产生 runtime-backed real lhs producer 或 instruction-level material evidence；默认应保持 false。
```

优先使用已有 current divergence artifact 或 `current_state.latest_compare_handoff_path_divergence_audit` 做离线归纳。只有当本地 current artifact 缺少必要字段，或 `current_state` 内嵌摘要不足以解释 handoff 后 edge 时，才允许新增一个 bounded runtime sidecar。若新增 runtime sidecar，必须只使用同 3 个固定候选，且只围绕 handoff edge / branch operand / exception edge 捕获事件，不做 material capture。

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

`.codex-skills/registry.json` 当前只登记两个 active skill，分别为：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Trace bounded branch operand or exception edge provenance
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 state：

```text
state_build_id=state_20260531_144509_d2e114f45b75
state_digest=d2e114f45b75080eadf84cfb6a85235ebc126abea6246dc295fbce5f0b7a9857
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 bottleneck：

```text
stage=compare_handoff_path_divergence_audit
blocker=candidate_dependent_non_reaching_path
reason=candidate_dependent_non_reaching_path
confidence=medium
```

current artifact：

```text
compare_handoff_path_divergence_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_path_divergence_audit\compare_handoff_path_divergence_audit.json
  sha256=50d18d9a64f512ec72cc9e560ed2175473c16e128583fc375f85409c6db1cbd3
```

注意：远端 GitHub 内容中不一定提交完整 `solve_reports/` artifact，这是允许的；Codex 本地执行时必须先验证该 artifact 路径是否存在。如果本地 artifact 缺失，不得把 stale / missing artifact 当作当前证据；应优先使用 `current_state.latest_compare_handoff_path_divergence_audit` 的内嵌摘要，必要时有界重建 project_state：

```text
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
```

若本地 `solve_reports` 与 current artifact 都不可用，必须报告 `BLOCKED`，不要猜测。

上一轮 divergence 结果：

```text
candidate_count=3
runtime_backed_count=3
common_prefix_events=predecessor_handoff_call -> handoff_helper_entry
first_divergence_after=handoff_helper_entry
first_divergence_classification=candidate_dependent_handoff_exit_after_helper_entry
exception_subset_classification=exception_edge_shared_for_subset
branch_subset_classification=branch_guard_or_silent_non_reaching_path
overall_classification=candidate_dependent_non_reaching_path
next_bounded_action=branch_operand_provenance_or_exception_edge_audit
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141 -> exception_path / exception_unwind_before_compare
5a3e7f46ddd474d041414141414141 -> exception_path / exception_unwind_before_compare
78d540b49c59076f41414141414141 -> branch_guard_or_silent_non_reaching_path / branch_guard_before_compare
```

已知 exception evidence：

```text
candidate 78d540b49c59077041414141414141:
  process_exception module_offset=0x1913
  exception.address=0xf41913
  exception.memory=0x5305154b
  previous_event=handoff_helper_entry

candidate 5a3e7f46ddd474d041414141414141:
  process_exception module_offset=0x1913
  exception.address=0xf41913
  exception.memory=0x820004
  previous_event=handoff_helper_entry
```

已知 branch/silent evidence：

```text
candidate 78d540b49c59076f41414141414141:
  event_sequence=predecessor_handoff_call -> handoff_helper_entry
  process_exception_observed=false
  first_compare_successor_observed=false
  actual_compare_observed=false
  minimal_explanation=handoff_helper_entry observed, then no process_exception, first_compare_successor, or actual_compare
```

已知 handoff return context 是 candidate-dependent：

```text
handoff_helper_entry_return_address:
  78d540b49c59077041414141414141 -> 0xc5052f
  5a3e7f46ddd474d041414141414141 -> 0x2ae052f
  78d540b49c59076f41414141414141 -> 0xfff4052f
return_context_candidate_dependent=true
```

已知禁止结论：

```text
1. fallback compare args 仍不能当作 provenance。
2. old [ebp-0x1170] 不能复用为 real LHS source。
3. Base64/RC4 breakpoint probe 仍被 negative_results 阻断，直到 real lhs producer 被证明。
4. 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 不能当作 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
```

## 3. Do Not Do

严禁：

```text
1. 不回旧 sample_solver 盲搜。
2. 不扩大 beam / topN / budget / timeout。
3. 不新增候选池。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不做 Base64/RC4 material capture。
6. 不做 crypto hook、material hook、Base64/RC4 hook。
7. 不重复 exact2 basin value-pool evaluation。
8. 不重复 H1/H3 fixed boundary contrast set。
9. 不重复 current 5-candidate transform trace consistency audit。
10. 不重复 compare_handoff_exit_classifier_audit 只为得到同样 classification。
11. 不重复 compare_handoff_path_divergence_audit 只为复述上一轮结果。
12. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
13. 不复用旧 [ebp-0x1170] 作为 real LHS source。
14. 不读取完整 solve_reports/。
15. 不读取完整 PROJECT_PROGRESS_LOG.txt。
16. 不修改 .codex-skills/。
17. 不修改 sample_corpus/reverse/。
18. 不修改 reverse_agent/harness.py。
19. 不提交完整 solve_reports/。
20. 不新增 rc4enc 静态分析报告。
21. 不把 stale/missing artifact 当 current evidence。
22. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 只有在 current divergence artifact / current_state 内嵌摘要不足以完成 edge/operand provenance 时，才允许新增 bounded runtime sidecar。
2. 必须使用同 3 个固定候选。
3. 只允许 handoff edge surface：predecessor_handoff_call / handoff_helper_entry / process_exception / first_compare_successor / actual_compare / 必要的 branch operand、return context、exception context。
4. 不允许 candidate search、material hooks、crypto hooks、Base64/RC4 hooks。
5. 不允许扩大 timeout / budget 来掩盖 instrumentation gap；若证据不足，应分类为 hook_surface_or_instrumentation_gap。
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

必须有界读取或验证：

```text
project_state.current_state.latest_compare_handoff_path_divergence_audit
project_state.artifact_index.latest_artifacts_v2.compare_handoff_path_divergence_audit
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_path_divergence_audit/compare_handoff_path_divergence_audit.json
```

允许有界读取上一轮 source classifier artifact，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/compare_handoff_exit_classifier_audit.json
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
reverse_agent/olly_scripts/compare_handoff_edge_operand_provenance_audit.py
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
5. 是否验证 .codex-skills/registry.json 中 active skills 匹配。
6. 是否保持同 3 个固定候选。
7. 是否没有扩大候选、beam、topN、budget、timeout。
8. 是否没有运行 Base64/RC4 breakpoint probe。
9. 是否没有运行 material capture / crypto hook。
10. 是否没有回旧 sample_solver。
11. 是否没有读取完整 solve_reports/。
12. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
13. 是否没有修改 .codex-skills/。
14. 是否没有修改 sample_corpus/reverse/。
15. 是否没有把 stale/missing artifact 当 current。
16. 是否验证 compare_handoff_path_divergence_audit freshness=current。
17. 若本地 artifact 缺失，是否明确使用 current_state 内嵌摘要或报告 BLOCKED。
18. 是否输出 compare_handoff_edge_operand_provenance_audit 或等价 artifact。
19. artifact 是否包含 per-candidate handoff edge summary。
20. artifact 是否包含 branch operand / condition provenance 或明确 schema/runtime gap。
21. artifact 是否包含 exception edge provenance 或明确 schema/runtime gap。
22. artifact 是否保留两个 exception candidates 的 exception address / memory / previous_event。
23. artifact 是否保留 branch_guard candidate 的 no-exception/no-successor/no-compare explanation。
24. artifact 是否给出 cross_candidate root-cause classification。
25. artifact 是否给出 next_bounded_action。
26. artifact_index 是否 additive 更新，不删除旧字段。
27. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
28. negative_results 是否未被重复违反。
29. lint-decision 是否通过。
30. lint-report 是否通过。
31. 相关 pytest 是否通过。
32. git diff --check 是否通过。
33. 是否写入 pytest_result.txt 且 decision_id/report_id/round_id 匹配。
34. 是否归档 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 首选：offline edge / operand provenance projection

先从 current divergence payload 或 `current_state.latest_compare_handoff_path_divergence_audit` 提取：

```text
candidate_hex
prior_classification
event_sequence
exception_summary
return_address_summary
first_divergence_role
minimal_explanation
process_exception_observed
first_compare_successor_observed
actual_compare_observed
scripted_hook_status
scripted_returncode
cross_candidate.common_prefix_events
cross_candidate.first_divergence_after
cross_candidate.first_divergence_classification
cross_candidate.exception_subset_classification
cross_candidate.branch_subset_classification
```

生成 `compare_handoff_edge_operand_provenance_audit.json`，最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "source_artifacts": [
    "compare_handoff_path_divergence_audit",
    "compare_handoff_exit_classifier_audit"
  ],
  "candidate_count": 3,
  "runtime_backed_count": 3,
  "fixed_candidates": ["..."],
  "candidates": [
    {
      "candidate_hex": "...",
      "prior_divergence_role": "exception_path | branch_guard_or_silent_non_reaching_path",
      "common_prefix_observed": ["predecessor_handoff_call", "handoff_helper_entry"],
      "handoff_helper_entry_context": {
        "return_address_module_offset": "...",
        "return_context_candidate_dependent": true
      },
      "exception_edge_summary": {
        "observed": true,
        "module_offset": "0x1913",
        "address": "...",
        "memory": "...",
        "previous_event": "handoff_helper_entry",
        "candidate_dependent_memory": true
      },
      "branch_operand_summary": {
        "observed": false,
        "operand_source": "unknown",
        "classification": "not_observed | candidate_dependent | schema_gap | instrumentation_gap"
      },
      "post_entry_probe_summary": {
        "successor_observed": false,
        "actual_compare_observed": false,
        "process_exception_observed": true
      },
      "candidate_classification": "exception_edge_after_handoff | branch_guard_silent_after_handoff | instrumentation_gap"
    }
  ],
  "cross_candidate": {
    "common_prefix_events": ["predecessor_handoff_call", "handoff_helper_entry"],
    "first_divergence_after": "handoff_helper_entry",
    "return_context_candidate_dependent": true,
    "exception_edge_shared_for_subset": true,
    "branch_guard_candidate_count": 1,
    "root_cause_classification": "candidate_dependent_handoff_exit_edge_unresolved",
    "evidence_strength": "offline_projected | runtime_backed",
    "next_bounded_action": "..."
  },
  "breakpoint_probe_allowed": false,
  "candidate_generation_changed": false,
  "ranking_changed": false,
  "search_budget_changed": false,
  "beam_budget_topn_timeout_frontier_limit_expanded": false
}
```

离线 projection 可以接受的分类：

```text
candidate_dependent_handoff_exit_edge_unresolved
exception_edge_candidate_dependent_for_subset
branch_guard_silent_exit_unresolved
return_context_candidate_dependent_unresolved
hook_surface_or_instrumentation_gap
```

如果只复述上一轮 divergence 结果，没有新增 branch/exception/return-context 层面的 root-cause narrowing，则本轮不得标记 SUCCESS。

### 6.2 允许：bounded runtime sidecar

只有 offline projection 不足时，新增 sidecar：

```text
reverse_agent/olly_scripts/compare_handoff_edge_operand_provenance_audit.py
```

sidecar 只允许捕获：

```text
1. 0x2338 predecessor_handoff_call。
2. 0x1b50 handoff_helper_entry。
3. handoff_helper_entry 后的 return / branch / exception context。
4. 0x1913 process_exception context。
5. first_compare_successor / actual_compare 是否出现。
6. 必要的 register / stack / flags / branch operand 快照。
```

sidecar 不允许捕获：

```text
1. Base64/RC4 material。
2. crypto buffer。
3. candidate search output。
4. 新候选 ranking evidence。
5. 完整 solve_reports 遍历。
```

若无法稳定捕获 branch operand 或 exception edge，不要扩大预算；应在 artifact 中明确：

```text
branch_operand_summary.classification=schema_gap 或 instrumentation_gap
exception_edge_summary.classification=schema_gap 或 instrumentation_gap
next_bounded_action=hook_surface_correction 或 instruction_boundary_audit
```

### 6.3 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_edge_operand_provenance_audit
artifact_index.latest_artifacts_v2.compare_handoff_edge_operand_provenance_audit
current_state.latest_compare_handoff_edge_operand_provenance_audit
current_state.current_bottleneck.stage=compare_handoff_edge_operand_provenance_audit
```

不要删除或重命名旧字段。不要把当前 candidate、artifact path、runtime metric 写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"
python -m pytest -q tests\test_project_state.py -k "handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果新增 runtime sidecar，还必须运行：

```text
python -m py_compile reverse_agent\olly_scripts\compare_handoff_edge_operand_provenance_audit.py
```

建议补充完整相关测试：

```text
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m pytest -q tests\test_project_state.py
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_handoff_edge_operand_provenance_audit
round_id=round_20260601_handoff_edge_operand_provenance_audit
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. 本地 current divergence artifact 缺失，且 current_state 内嵌摘要不足以生成 bounded audit。
2. artifact_index.latest_artifacts_v2 中 compare_handoff_path_divergence_audit 不是 current。
3. 3 个固定候选无法全部复现或被替换。
4. 需要新增候选、扩大 beam/topN/budget/timeout 才能继续。
5. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
6. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
7. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
8. branch operand / exception edge 无法从现有 schema 或 bounded sidecar 捕获；此时输出 instrumentation_gap / schema_gap 分类并停止。
9. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据，不得声称 ACCEPTED。

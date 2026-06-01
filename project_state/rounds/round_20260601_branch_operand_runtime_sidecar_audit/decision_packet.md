```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_branch_operand_runtime_sidecar_audit",
  "round_id": "round_20260601_branch_operand_runtime_sidecar_audit",
  "based_on_state_build_id": "state_20260601_043626_759cb075799e",
  "based_on_state_digest": "759cb075799e71e94ceb6076765b78a8d67bfc61ccfdb3ea1928836b2bdd460a",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**。上一轮 `decision_20260601_handoff_edge_operand_provenance_audit` 已完成有界 offline edge/operand projection，但 Codex 报告为 `PARTIAL / NEEDS_REVIEW`，原因是 branch_guard candidate 的 `branch_operand_summary.classification=schema_gap`：已有 artifact 没有捕获 branch operand 或 flags。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

本轮目标不是求最终 flag，不是重复 offline projection，也不是扩大搜索。本轮只补上一轮缺失的最小证据：在同 3 个固定候选上，定位 `handoff_helper_entry` 之后 branch_guard / silent non-reaching candidate 的 branch operand、flags、return target 或 instruction-boundary gap。

## 1. Goal

新增或生成一个有界 artifact，建议 artifact 名称：

```text
compare_handoff_branch_operand_runtime_audit.json
```

核心问题：

```text
上一轮已经确认：
1. 3 个固定候选共同到达 predecessor_handoff_call -> handoff_helper_entry。
2. 两个 candidate 随后进入 process_exception。
3. 一个 candidate 进入 branch_guard_or_silent_non_reaching_path：无 process_exception、无 first_compare_successor、无 actual_compare。
4. branch_operand_summary 仍是 schema_gap。

本轮必须回答：
branch_guard candidate 在 handoff_helper_entry 后到底因哪个 branch operand / flags / return target / hook gap 没有继续进入 exception 或 compare path？
```

本轮必须输出：

```text
1. per-candidate handoff_helper_entry 后的 bounded control-flow evidence。
2. branch_guard candidate 的 branch operand / flags / return target / next basic block 证据；若无法捕获，必须明确 instrumentation_gap 或 instruction_boundary_gap。
3. 两个 exception candidates 是否共享同一 exception edge，以及该 edge 与 branch_guard candidate 的差异。
4. handoff_helper_entry_return_address 是否是真实 return address、候选相关伪值、栈读取错误，还是 instrumentation/schema 问题。
5. cross-candidate root-cause classification。
6. next_bounded_action，必须是 branch operand provenance、return-target correction、exception-edge confirmation、或 hook-surface repair 中的一个。
```

如果能用静态 instruction-boundary audit 解释 branch operand 缺口，可以不运行 runtime sidecar。若静态信息不足，则允许新增一个 bounded runtime sidecar，只围绕 handoff edge / branch operand / flags / return target 捕获，不允许 material capture。

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
Trace bounded branch operand runtime sidecar or instruction boundary
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 state：

```text
state_build_id=state_20260601_043626_759cb075799e
state_digest=759cb075799e71e94ceb6076765b78a8d67bfc61ccfdb3ea1928836b2bdd460a
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 bottleneck：

```text
stage=compare_handoff_edge_operand_provenance_audit
blocker=candidate_dependent_handoff_exit_edge_unresolved
reason=candidate_dependent_handoff_exit_edge_unresolved
confidence=medium
```

current artifact：

```text
compare_handoff_edge_operand_provenance_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_edge_operand_provenance_audit\compare_handoff_edge_operand_provenance_audit.json
  sha256=6e5408b45f49e0013b5edd6008cac2bca22fee6876c27bcd2eb78172edb4c167
```

上一轮结果：

```text
report_status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
root_cause_classification=candidate_dependent_handoff_exit_edge_unresolved
schema_gap_fields=branch_operand_summary
next_bounded_action=bounded_branch_operand_runtime_sidecar_or_instruction_boundary_audit
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141 -> exception_edge_after_handoff
5a3e7f46ddd474d041414141414141 -> exception_edge_after_handoff
78d540b49c59076f41414141414141 -> branch_guard_silent_after_handoff
```

已知 exception evidence：

```text
candidate 78d540b49c59077041414141414141:
  exception_edge_summary.classification=candidate_dependent
  process_exception module_offset=0x1913
  exception.address=0xf41913
  exception.memory=0x5305154b
  previous_event=handoff_helper_entry

candidate 5a3e7f46ddd474d041414141414141:
  exception_edge_summary.classification=candidate_dependent
  process_exception module_offset=0x1913
  exception.address=0xf41913
  exception.memory=0x820004
  previous_event=handoff_helper_entry
```

已知 branch/silent evidence：

```text
candidate 78d540b49c59076f41414141414141:
  candidate_classification=branch_guard_silent_after_handoff
  branch_operand_summary.classification=schema_gap
  branch_operand_summary.observed=false
  operand_source=unknown
  condition=""
  process_exception_observed=false
  successor_observed=false
  actual_compare_observed=false
  minimal_explanation=handoff_helper_entry observed, then no process_exception, first_compare_successor, or actual_compare; prior artifact did not capture branch operand or flags
```

已知 return context 仍需校验：

```text
handoff_helper_entry_return_address:
  78d540b49c59077041414141414141 -> 0xc5052f
  5a3e7f46ddd474d041414141414141 -> 0x2ae052f
  78d540b49c59076f41414141414141 -> 0xfff4052f
return_context_candidate_dependent=true
```

这些 return address 值看起来不像普通模块内线性返回地址。本轮必须判定它们是：

```text
1. 真实 candidate-dependent return target；
2. 异常/保护机制导致的候选相关伪 return value；
3. hook 读取栈顶字段错误；
4. instrumentation/schema gap。
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
12. 不重复 compare_handoff_edge_operand_provenance_audit 的 offline projection 只为得到同样 schema_gap。
13. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
14. 不复用旧 [ebp-0x1170] 作为 real LHS source。
15. 不读取完整 solve_reports/。
16. 不读取完整 PROJECT_PROGRESS_LOG.txt。
17. 不修改 .codex-skills/。
18. 不修改 sample_corpus/reverse/。
19. 不修改 reverse_agent/harness.py。
20. 不提交完整 solve_reports/。
21. 不新增 rc4enc 静态分析报告。
22. 不把 stale/missing artifact 当 current evidence。
23. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 handoff edge surface：predecessor_handoff_call / handoff_helper_entry / process_exception / first_compare_successor / actual_compare / 必要的 branch operand、flags、return target、next block context。
3. 不允许 candidate search、material hooks、crypto hooks、Base64/RC4 hooks。
4. 不允许扩大 timeout / budget 来掩盖 instrumentation gap。
5. 若 branch operand / flags 仍无法捕获，应输出 instrumentation_gap 或 instruction_boundary_gap，并停止。
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
project_state.current_state.latest_compare_handoff_edge_operand_provenance_audit
project_state.artifact_index.latest_artifacts_v2.compare_handoff_edge_operand_provenance_audit
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_edge_operand_provenance_audit/compare_handoff_edge_operand_provenance_audit.json
```

允许有界读取上游 current artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_path_divergence_audit/compare_handoff_path_divergence_audit.json
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
reverse_agent/olly_scripts/compare_handoff_branch_operand_runtime_audit.py
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
16. 是否验证 compare_handoff_edge_operand_provenance_audit freshness=current。
17. 是否输出 compare_handoff_branch_operand_runtime_audit 或等价 artifact。
18. artifact 是否包含 per-candidate branch/flags/return-target evidence。
19. artifact 是否明确 branch_guard candidate 的 operand_source、flags、condition 或 gap classification。
20. artifact 是否解释两个 exception candidates 与 branch_guard candidate 的 edge 差异。
21. artifact 是否判定 handoff_helper_entry_return_address 的可信性。
22. artifact 是否给出 cross_candidate root-cause classification。
23. artifact 是否给出 next_bounded_action。
24. artifact_index 是否 additive 更新，不删除旧字段。
25. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
26. negative_results 是否未被重复违反。
27. lint-decision 是否通过。
28. lint-report 是否通过。
29. 相关 pytest 是否通过。
30. git diff --check 是否通过。
31. 是否写入 pytest_result.txt 且 decision_id/report_id/round_id 匹配。
32. 是否归档 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 首选：instruction-boundary audit

先做有界静态/结构化审计，不遍历完整 solve_reports：

```text
1. 读取 current edge_operand artifact 或 current_state.latest_compare_handoff_edge_operand_provenance_audit。
2. 读取 source divergence artifact 的 3 个 candidate event sequence。
3. 定位 handoff_helper_entry 后可观察到的 next edge、return target、exception edge。
4. 判断现有 return_address 字段是否可信：是否落在模块边界、是否与 expected call/return frame 一致、是否可能是栈顶误读。
5. 若可以从现有 instruction boundary / hook surface 判断缺失原因，生成 artifact 并停止。
```

### 6.2 允许：bounded runtime sidecar

若 6.1 无法解释 branch operand / flags，则新增 sidecar：

```text
reverse_agent/olly_scripts/compare_handoff_branch_operand_runtime_audit.py
```

sidecar 只允许捕获：

```text
1. 0x2338 predecessor_handoff_call。
2. 0x1b50 handoff_helper_entry。
3. handoff_helper_entry 时 ESP/EBP/EIP、stack top words、candidate-visible return target。
4. handoff_helper_entry 后有限步内的 branch instruction、EFLAGS、condition outcome、next EIP。
5. 0x1913 process_exception context。
6. first_compare_successor / actual_compare 是否出现。
```

sidecar 不允许捕获：

```text
1. Base64/RC4 material。
2. crypto buffer。
3. candidate search output。
4. 新候选 ranking evidence。
5. 完整 solve_reports 遍历。
```

sidecar 输出最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "source_artifact": "compare_handoff_edge_operand_provenance_audit",
  "candidate_count": 3,
  "runtime_backed_count": 3,
  "fixed_candidates": ["..."],
  "candidates": [
    {
      "candidate_hex": "...",
      "prior_classification": "exception_edge_after_handoff | branch_guard_silent_after_handoff",
      "handoff_entry_observed": true,
      "entry_context": {
        "eip": "...",
        "esp": "...",
        "ebp": "...",
        "stack_top_words": [],
        "return_target_observed": "...",
        "return_target_trust": "trusted | suspicious | schema_gap | instrumentation_gap"
      },
      "branch_operand_evidence": {
        "observed": false,
        "branch_eip": "",
        "instruction": "",
        "eflags": "",
        "condition": "",
        "outcome": "taken | not_taken | unknown",
        "operand_source": "",
        "classification": "candidate_dependent | not_candidate_dependent | not_observed | instruction_boundary_gap | instrumentation_gap"
      },
      "exception_edge_evidence": {
        "observed": false,
        "module_offset": "",
        "address": "",
        "memory": "",
        "classification": "candidate_dependent | not_observed | instrumentation_gap"
      },
      "post_entry_outcome": "exception_edge | branch_guard_silent | compare_successor | actual_compare | instrumentation_gap"
    }
  ],
  "cross_candidate": {
    "root_cause_classification": "branch_operand_candidate_dependent | return_target_candidate_dependent | exception_edge_candidate_dependent_for_subset | instruction_boundary_gap | instrumentation_gap",
    "branch_guard_explained": true,
    "next_bounded_action": "..."
  },
  "breakpoint_probe_allowed": false,
  "candidate_generation_changed": false,
  "ranking_changed": false,
  "search_budget_changed": false,
  "beam_budget_topn_timeout_frontier_limit_expanded": false
}
```

如果 sidecar 仍无法捕获 branch operand / flags，不要扩大预算；必须输出：

```text
root_cause_classification=instruction_boundary_gap 或 instrumentation_gap
next_bounded_action=hook_surface_correction 或 static_instruction_boundary_audit
```

### 6.3 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_branch_operand_runtime_audit
artifact_index.latest_artifacts_v2.compare_handoff_branch_operand_runtime_audit
current_state.latest_compare_handoff_branch_operand_runtime_audit
current_state.current_bottleneck.stage=compare_handoff_branch_operand_runtime_audit
```

不要删除或重命名旧字段。不要把当前 candidate、artifact path、runtime metric 写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"
python -m pytest -q tests\test_project_state.py -k "branch_operand_runtime or handoff_edge_operand or handoff_path_divergence or handoff_exit_classifier"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果新增 runtime sidecar，还必须运行：

```text
python -m py_compile reverse_agent\olly_scripts\compare_handoff_branch_operand_runtime_audit.py
```

建议补充完整相关测试：

```text
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m pytest -q tests\test_project_state.py
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_branch_operand_runtime_sidecar_audit
round_id=round_20260601_branch_operand_runtime_sidecar_audit
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。若 archive-round 后最终 status/lint-report 未重跑，不得在 summary tests_ran 中声称已重跑。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. 本地 current edge_operand artifact 缺失，且 current_state 内嵌摘要不足以生成 bounded audit。
2. artifact_index.latest_artifacts_v2 中 compare_handoff_edge_operand_provenance_audit 不是 current。
3. 3 个固定候选无法全部复现或被替换。
4. 需要新增候选、扩大 beam/topN/budget/timeout 才能继续。
5. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
6. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
7. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
8. branch operand / flags / return target 无法从 instruction-boundary audit 或 bounded sidecar 捕获；此时输出 instrumentation_gap / instruction_boundary_gap 分类并停止。
9. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据，不得声称 ACCEPTED。

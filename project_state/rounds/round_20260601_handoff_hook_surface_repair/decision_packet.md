```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_handoff_hook_surface_repair",
  "round_id": "round_20260601_handoff_hook_surface_repair",
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

本轮回到 **samplereverse 逆向解题主线**，但只做有界 `hook_surface_repair`。上一轮 `decision_20260601_report_status_consistency_rework` 已修复 report / pytest / lint 状态一致性；再上一轮 `decision_20260601_branch_operand_runtime_sidecar_audit` 将当前 bottleneck 明确为 `instruction_boundary_gap`。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

本轮目标不是求最终 flag，不是继续搜索，不是运行 Base64/RC4 probe。本轮只修复 handoff 后观察面：让后续有界审计能够捕获 `handoff_helper_entry` 之后的 branch instruction、EFLAGS、condition outcome、next EIP / next block、return-target trust，而不是继续产出同样的 `instruction_boundary_gap`。

## 1. Goal

新增或生成一个有界 artifact，建议 artifact 名称：

```text
compare_handoff_hook_surface_repair_audit.json
```

核心问题：

```text
当前 compare_handoff_branch_operand_runtime_audit 已确认：
1. 3 个固定候选仍共同到达 handoff_helper_entry。
2. 两个候选进入 exception_edge。
3. branch_guard candidate 仍无 branch_eip / instruction / eflags / condition / next block。
4. root_cause_classification=instruction_boundary_gap。
5. return_target_trust=suspicious。

本轮必须修复或界定 hook surface：为什么现有 hook 只能看到 handoff_helper_entry，却看不到后续 branch/flags/next block？
```

本轮必须输出：

```text
1. 当前 hook surface 的覆盖范围：predecessor_handoff_call、handoff_helper_entry、process_exception、compare successor、actual compare。
2. handoff_helper_entry 后缺失 branch operand 的最小原因：hook placement 错误、single-step 缺失、return target 误读、instruction boundary 错误、anti-debug/exception path、或工具 schema 缺失。
3. 是否需要新增一个 bounded post-entry stepping sidecar。
4. 如果新增 sidecar，必须只捕获同 3 个固定候选在 handoff_helper_entry 后的有限步 branch/flags/next-EIP，不捕获 material。
5. 对 return_target_trust=suspicious 的最小判定：真实候选相关返回、伪 return value、栈顶误读、还是 instrumentation gap。
6. next_bounded_action：post_entry_step_runtime_audit、return_target_correction、exception_edge_confirmation、或 static_instruction_boundary_fix。
```

若能通过静态 hook-boundary 审计解释缺口，可以不新增 runtime sidecar。若不能解释，允许新增 bounded post-entry stepping sidecar，但必须严格限于观察 control-flow surface。

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

当前 branch audit 结论：

```text
root_cause_classification=instruction_boundary_gap
branch_guard_explained=false
return_context_candidate_dependent=true
return_target_trust=suspicious
exception_edge_shared_for_subset=true
exception_edge_candidate_dependent_memory=true
next_bounded_action=hook_surface_repair
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141 -> exception_edge_after_handoff
5a3e7f46ddd474d041414141414141 -> exception_edge_after_handoff
78d540b49c59076f41414141414141 -> branch_guard_silent_after_handoff / instruction_boundary_gap
```

branch_guard candidate 当前缺失字段：

```text
branch_eip=""
instruction=""
eflags=""
condition=""
operand_source=unknown
outcome=unknown
post_entry_outcome=instruction_boundary_gap
return_target_observed=0xfff4052f
return_target_trust=suspicious
```

已知禁止结论：

```text
1. fallback compare args 仍不能当作 provenance。
2. old [ebp-0x1170] 不能复用为 real LHS source。
3. Base64/RC4 breakpoint probe 仍被 negative_results 阻断，直到 real lhs producer 被证明。
4. 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 不能当作 Base64/RC4 material producer，除非本轮产生新的 instruction-level semantic evidence。
5. 上一轮 report 状态一致性已修复；不要再做同一 rework。
```

## 3. Do Not Do

严禁：

```text
1. 不求最终 flag。
2. 不回旧 sample_solver 盲搜。
3. 不新增候选池。
4. 不扩大 beam / topN / budget / timeout / frontier limit。
5. 不运行 Base64/RC4 breakpoint probe。
6. 不做 Base64/RC4 material capture。
7. 不做 crypto hook、material hook、Base64/RC4 hook。
8. 不重复 compare_handoff_branch_operand_runtime_audit 只为得到同样 instruction_boundary_gap。
9. 不重复 report_status_consistency_rework。
10. 不把 stale/missing artifact 当 current evidence。
11. 不伪造 branch_eip / eflags / instruction / condition。
12. 不读取完整 solve_reports/。
13. 不读取完整 PROJECT_PROGRESS_LOG.txt。
14. 不修改 .codex-skills/。
15. 不修改 sample_corpus/reverse/。
16. 不修改 reverse_agent/harness.py。
17. 不提交完整 solve_reports/。
18. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 control-flow surface：handoff_helper_entry 后有限步 EIP、instruction、EFLAGS、branch condition、next EIP、process_exception、compare successor、actual compare。
3. 不允许读取或保存 Base64/RC4 material、crypto buffer、candidate ranking evidence。
4. 不允许扩大预算来掩盖 instrumentation gap。
5. 若有限步仍无法捕获，必须输出 hook_surface_unresolved 或 instrumentation_gap，并停止。
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

必须读取或验证：

```text
.codex-skills/registry.json
project_state/rounds/round_20260601_report_status_consistency_rework/round_manifest.json
project_state.current_state.latest_compare_handoff_branch_operand_runtime_audit
project_state.artifact_index.latest_artifacts_v2.compare_handoff_branch_operand_runtime_audit
```

允许有界读取上游 current artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_branch_operand_runtime_audit/compare_handoff_branch_operand_runtime_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_edge_operand_provenance_audit/compare_handoff_edge_operand_provenance_audit.json
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

只有需要新增 bounded post-entry stepping sidecar 时，才允许新增/修改：

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
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
5. .codex-skills/registry.json 是否仍只登记这两个 active skills。
6. 是否验证 report_status_consistency_rework 已完成且当前 report/pytest 一致。
7. 是否保持同 3 个固定候选。
8. 是否没有新增候选、扩大 beam/topN/budget/timeout。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/、sample_corpus/reverse/、harness.py、sample_solver.py。
13. 是否验证 compare_handoff_branch_operand_runtime_audit freshness=current。
14. 是否输出 compare_handoff_hook_surface_repair_audit 或等价 artifact。
15. artifact 是否解释当前 hook surface 为什么缺 branch operand / flags / next block。
16. artifact 是否判定 return_target_trust=suspicious 的最小原因或下一步校正路径。
17. 若新增 sidecar，是否只捕获有限 control-flow surface。
18. 若未新增 sidecar，是否给出足够的 static/instruction-boundary reason。
19. artifact 是否给出 next_bounded_action。
20. artifact_index 是否 additive 更新，不删除旧字段。
21. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
22. negative_results 是否未被重复违反。
23. lint-decision 是否通过。
24. lint-report 是否通过。
25. 相关 pytest 是否通过。
26. git diff --check 是否通过。
27. pytest_result.txt 是否与真实命令结果一致。
28. codex_report_summary 是否与当前 decision_id 匹配。
29. 是否归档本轮 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 首选：hook-surface static/instruction-boundary audit

先做有界静态/结构化审计：

```text
1. 从 current branch operand runtime artifact 读取 3 个固定候选的 entry_context、branch_operand_evidence、exception_edge_evidence、post_entry_outcome。
2. 对比上游 exit/path/edge artifacts，确认 hook surface 到底停在 handoff_helper_entry 还是 post-entry stepping 缺失。
3. 判断 return_target_observed 是否来自真实 call-return frame、栈顶误读、异常伪值、或 hook schema 字段误命名。
4. 明确现有 hook surface 缺哪个观测点：post-entry single-step、return-address correction、branch breakpoint、next-EIP sampling、或 exception continuation sampling。
5. 若静态审计足够，生成 compare_handoff_hook_surface_repair_audit.json 并停止。
```

### 6.2 允许：bounded post-entry stepping sidecar

若 6.1 不能解释 gap，则新增 sidecar：

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
```

sidecar 只允许捕获：

```text
1. 0x2338 predecessor_handoff_call。
2. 0x1b50 handoff_helper_entry。
3. handoff_helper_entry 时 EIP/ESP/EBP、stack top words、return target candidate。
4. handoff_helper_entry 后有限步 EIP、disasm/instruction text、EFLAGS、branch condition、branch outcome、next EIP。
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
  "source_artifacts": [
    "compare_handoff_branch_operand_runtime_audit",
    "compare_handoff_edge_operand_provenance_audit"
  ],
  "candidate_count": 3,
  "fixed_candidates": ["..."],
  "hook_surface_repair": {
    "surface_classification": "static_boundary_explained | post_entry_step_added | return_target_schema_correction | hook_surface_unresolved",
    "missing_observation": "branch_instruction | eflags | next_eip | return_target | exception_continuation",
    "repair_applied": true,
    "repair_type": "static_schema | runtime_sidecar | no_code_change_gap_classification"
  },
  "candidates": [
    {
      "candidate_hex": "...",
      "post_entry_events": [],
      "branch_observation": {
        "observed": false,
        "branch_eip": "",
        "instruction": "",
        "eflags": "",
        "condition": "",
        "outcome": "unknown",
        "next_eip": "",
        "classification": "candidate_dependent | not_observed | hook_surface_unresolved | instrumentation_gap"
      },
      "return_target_observation": {
        "observed": true,
        "value": "...",
        "trust": "trusted | suspicious | corrected | instrumentation_gap",
        "reason": "..."
      },
      "post_entry_outcome": "exception_edge | branch_guard_silent | compare_successor | actual_compare | hook_surface_gap"
    }
  ],
  "cross_candidate": {
    "root_cause_classification": "hook_surface_repaired | return_target_schema_gap | branch_operand_candidate_dependent | hook_surface_unresolved | instrumentation_gap",
    "branch_guard_explained": false,
    "next_bounded_action": "..."
  },
  "breakpoint_probe_allowed": false,
  "candidate_generation_changed": false,
  "ranking_changed": false,
  "search_budget_changed": false,
  "beam_budget_topn_timeout_frontier_limit_expanded": false
}
```

如果 sidecar 仍无法捕获 branch/flags/next EIP，不要扩大范围；必须输出：

```text
root_cause_classification=hook_surface_unresolved 或 instrumentation_gap
next_bounded_action=manual_static_instruction_boundary_audit 或 narrower_post_entry_breakpoint
```

### 6.3 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_hook_surface_repair_audit
artifact_index.latest_artifacts_v2.compare_handoff_hook_surface_repair_audit
current_state.latest_compare_handoff_hook_surface_repair_audit
current_state.current_bottleneck.stage=compare_handoff_hook_surface_repair_audit
```

不要删除或重命名旧字段。不要把当前 candidate、artifact path、runtime metric 写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "hook_surface_repair or branch_operand_runtime or handoff_edge_operand"
python -m pytest -q tests\test_project_state.py -k "hook_surface_repair or branch_operand_runtime or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果新增 runtime sidecar，还必须运行：

```text
python -m py_compile reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py
```

建议补充完整相关测试：

```text
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m pytest -q tests\test_project_state.py
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_handoff_hook_surface_repair
round_id=round_20260601_handoff_hook_surface_repair
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。不得把失败 lint 或 pending post-archive check 写成 PASSED。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. report_status_consistency_rework 未通过或当前 report/pytest 再次不一致。
2. artifact_index.latest_artifacts_v2 中 compare_handoff_branch_operand_runtime_audit 不是 current。
3. 3 个固定候选无法全部复现或被替换。
4. 需要新增候选、扩大 beam/topN/budget/timeout 才能继续。
5. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
6. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
7. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
8. hook surface 无法解释且 bounded sidecar 也无法捕获 post-entry branch/flags/next EIP；此时输出 hook_surface_unresolved / instrumentation_gap 并停止。
9. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

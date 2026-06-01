```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_post_entry_step_runtime_audit",
  "round_id": "round_20260601_post_entry_step_runtime_audit",
  "based_on_state_build_id": "state_20260601_061827_b914ea0b1647",
  "based_on_state_digest": "b914ea0b1647765ae3106b285fdb4bb20b23b35c34bcfe1c5c9c315026b06d51",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

上一轮 `decision_20260601_handoff_hook_surface_repair` 已将缺口界定为：现有 runtime-backed artifacts 到达 `handoff_helper_entry` 或 exception edge summary，但没有 post-entry single-step 的 branch instruction、EFLAGS、condition、next EIP / next block。下一步不得继续重复静态解释；必须新增一个有界 runtime sidecar，只观察 handoff helper entry 后有限步控制流 surface。

## 1. Goal

新增并运行一个有界 runtime sidecar，生成 artifact：

```text
compare_handoff_post_entry_step_runtime_audit.json
```

核心目标：

```text
在同 3 个固定候选上，从 predecessor_handoff_call / handoff_helper_entry 开始，捕获 handoff_helper_entry 后有限步 EIP、instruction/disasm、EFLAGS、branch condition/outcome、next EIP，以及 process_exception / compare successor / actual compare 是否出现。
```

本轮必须回答：

```text
1. branch_guard candidate 为什么在 handoff_helper_entry 后没有 branch operand：真实 silent path、post-entry branch 未单步、异常路径、return target 栈顶误读，还是 instrumentation gap。
2. 3 个固定候选在 handoff_helper_entry 后的首个分歧点是什么。
3. return_target_observed 是否可信：真实 call-return frame、candidate-dependent pseudo return、栈顶误读、还是 hook schema 误读。
4. 是否首次捕获 branch_eip / instruction / eflags / condition / next_eip。
5. 是否仍允许 Base64/RC4 breakpoint probe。默认仍不允许，除非本轮仅通过 control-flow surface 证明 real-lhs producer 或 material construction hook 的 instruction-level 连接。
6. next_bounded_action：return_target_correction、exception_edge_confirmation、compare_successor_reanchor、narrower_post_entry_breakpoint、manual_static_instruction_boundary_audit、或 real_lhs_producer_identification。
```

本轮不是求最终 flag，不做候选搜索，不做 material capture，不做 crypto hook。

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

当前 state：

```text
state_build_id=state_20260601_061827_b914ea0b1647
state_digest=b914ea0b1647765ae3106b285fdb4bb20b23b35c34bcfe1c5c9c315026b06d51
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Run bounded post-entry step runtime audit
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 bottleneck：

```text
stage=compare_handoff_hook_surface_repair_audit
reason=hook_surface_requires_post_entry_step
confidence=medium
```

current artifact：

```text
compare_handoff_hook_surface_repair_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_hook_surface_repair_audit\compare_handoff_hook_surface_repair_audit.json
  sha256=7dc7006a912e820972af7ac8746df86bb9a8333d192472f979c06f6020db79d2
```

上一轮 hook-surface repair 结论：

```text
classification=hook_surface_requires_post_entry_step
surface_classification=static_boundary_explained
missing_observation=branch_instruction
missing_observations=[branch_condition, branch_instruction, eflags, instruction_text, next_eip]
repair_type=no_code_change_gap_classification
post_entry_single_step=false
handoff_helper_entry=true
process_exception=true
compare_successor=false
actual_compare=false
return_target_trust=suspicious
return_target_minimal_reason=candidate-dependent, non-module-looking return targets require post-entry control-flow sampling or stack-frame correction before they can be trusted
next_bounded_action=post_entry_step_runtime_audit
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前关键观测：

```text
1. 两个候选到达 exception_edge_after_handoff / process_exception。
2. branch_guard candidate 在 handoff_helper_entry 后仍缺 branch_eip、instruction、eflags、condition、next_eip。
3. return_context_values=[0xc5052f, 0x2ae052f, 0xfff4052f]，跨候选变化且 non-module-looking。
4. Base64/RC4 static point discovery 仍未证明 instruction-confirmed Base64/RC4 hook；breakpoint_probe_allowed=false。
5. latest_artifacts_v2 中若 artifact 为 stale / missing，不得作为 current evidence。
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
8. 不读取或保存 Base64/RC4 material、crypto buffer、candidate ranking evidence。
9. 不把 post-entry step sidecar 变成 material probe。
10. 不重复 compare_handoff_hook_surface_repair_audit 只为再次得到 static_boundary_explained。
11. 不把 stale/missing artifact 当 current evidence。
12. 不伪造 branch_eip / eflags / instruction / condition / next_eip。
13. 不读取完整 solve_reports/。
14. 不读取完整 PROJECT_PROGRESS_LOG.txt。
15. 不修改 .codex-skills/。
16. 不修改 sample_corpus/reverse/。
17. 不修改 reverse_agent/harness.py。
18. 不修改 reverse_agent/sample_solver.py。
19. 不提交完整 solve_reports/。
20. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 control-flow surface：predecessor_handoff_call、handoff_helper_entry、post-entry 有限步 EIP/instruction/EFLAGS/branch condition/next EIP、process_exception、compare successor、actual compare。
3. 单候选最大 step 数必须有硬上限；建议 max_steps <= 32。
4. sidecar 不允许 dump 任意大内存，不允许保存 material bytes，不允许输出 candidate score/ranking。
5. 若有限步无法捕获，必须输出 hook_surface_unresolved 或 instrumentation_gap，并停止。
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
project_state.artifact_index.latest_artifacts_v2.compare_handoff_hook_surface_repair_audit
project_state.current_state.latest_compare_handoff_hook_surface_repair_audit
project_state.current_state.current_bottleneck
```

允许有界读取上游 current artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_hook_surface_repair_audit/compare_handoff_hook_surface_repair_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_branch_operand_runtime_audit/compare_handoff_branch_operand_runtime_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_edge_operand_provenance_audit/compare_handoff_edge_operand_provenance_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_path_divergence_audit/compare_handoff_path_divergence_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_exit_classifier_audit/compare_handoff_exit_classifier_audit.json
```

允许检查和修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
tests/test_compare_aware_search_strategy.py
reverse_agent/project_state.py
tests/test_project_state.py
project_state/artifact_index.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
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
6. 是否验证 compare_handoff_hook_surface_repair_audit freshness=current。
7. 是否保持同 3 个固定候选。
8. 是否没有新增候选、扩大 beam/topN/budget/timeout/frontier_limit。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/、sample_corpus/reverse/、harness.py、sample_solver.py。
13. 是否新增或运行 compare_handoff_post_entry_step_audit.py。
14. runtime sidecar 是否只捕获有限 control-flow surface。
15. artifact 是否包含每个固定候选的 post_entry_events。
16. artifact 是否包含 branch_observation：branch_eip、instruction、eflags、condition、outcome、next_eip、classification。
17. artifact 是否包含 return_target_observation：observed、value、trust、reason。
18. artifact 是否说明 3 个候选的首个分歧点。
19. artifact 是否说明 branch_guard candidate 的 gap 是否被解释。
20. artifact 是否明确 breakpoint_probe_allowed=false，除非有新的 instruction-level control-flow 证据解除 gate。
21. artifact_index 是否 additive 更新，不删除旧字段。
22. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
23. negative_results 是否未被重复违反。
24. lint-decision 是否通过；若执行后 state rebuild 导致 digest mismatch，必须标记 PARTIAL/NEEDS_REVIEW，不得写 SUCCESS/ACCEPTED。
25. lint-report 是否通过。
26. 相关 pytest 是否通过。
27. git diff --check 是否通过。
28. pytest_result.txt 是否与真实命令结果一致。
29. codex_report_summary 是否与当前 decision_id 匹配。
30. 是否归档本轮 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 新增 bounded post-entry step sidecar

新增或完善：

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
```

sidecar 最小行为：

```text
1. 固定读取 3 个候选，不从搜索器生成新候选。
2. 在 predecessor_handoff_call 和 handoff_helper_entry 处记录 EIP/ESP/EBP、stack top words、return address candidate。
3. 从 handoff_helper_entry 后执行有限步 single-step，max_steps 必须有硬上限，建议 <= 32。
4. 每步记录：step_index、eip、module_offset、instruction/disasm、eflags、is_branch、branch_condition、branch_taken/outcome、next_eip。
5. 记录 process_exception、compare successor、actual compare 是否出现及出现顺序。
6. 对 branch_guard candidate 特别记录 post_entry_outcome 是否从 instruction_boundary_gap 收敛到 branch_observed、exception_edge、compare_successor、actual_compare 或 instrumentation_gap。
```

sidecar 禁止行为：

```text
1. 不 dump Base64/RC4 material。
2. 不 dump crypto buffer。
3. 不生成 candidate search output。
4. 不输出 ranking / distance / score。
5. 不遍历完整 solve_reports。
6. 不扩大 runtime budget 来掩盖 instrumentation gap。
```

### 6.2 Strategy 集成

在 `CompareAwareSearchStrategy` 中新增有界入口，建议命名：

```text
compare_handoff_post_entry_step_runtime_audit
```

该入口只负责：

```text
1. 准备固定候选与 sidecar 参数。
2. 调用 sidecar 或在缺少 Olly 环境时生成清晰 blocked artifact。
3. 解析 sidecar 输出为 compare_handoff_post_entry_step_runtime_audit.json。
4. 不触发 candidate generation、guided pool、SMT、frontier search、material probe、Base64/RC4 probe。
```

### 6.3 Artifact schema

新 artifact 最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "source_artifacts": [
    "compare_handoff_hook_surface_repair_audit",
    "compare_handoff_branch_operand_runtime_audit",
    "compare_handoff_edge_operand_provenance_audit"
  ],
  "candidate_count": 3,
  "fixed_candidates": ["..."],
  "runtime_scope": {
    "sidecar": "compare_handoff_post_entry_step_audit.py",
    "max_steps_per_candidate": 32,
    "material_capture_allowed": false,
    "crypto_hook_allowed": false,
    "breakpoint_probe_allowed": false
  },
  "candidates": [
    {
      "candidate_hex": "...",
      "entry_context": {
        "predecessor_handoff_call_observed": false,
        "handoff_helper_entry_observed": false,
        "eip": "",
        "esp": "",
        "ebp": "",
        "stack_top_words": [],
        "return_target_candidate": ""
      },
      "post_entry_events": [],
      "branch_observation": {
        "observed": false,
        "branch_eip": "",
        "instruction": "",
        "eflags": "",
        "condition": "",
        "outcome": "unknown",
        "next_eip": "",
        "classification": "not_observed | branch_observed | instrumentation_gap | exception_before_branch | compare_successor_before_branch"
      },
      "return_target_observation": {
        "observed": false,
        "value": "",
        "trust": "trusted | suspicious | corrected | stack_top_misread | instrumentation_gap",
        "reason": ""
      },
      "post_entry_outcome": "branch_observed | exception_edge | compare_successor | actual_compare | instrumentation_gap | hook_surface_unresolved"
    }
  ],
  "cross_candidate": {
    "first_divergence_point": "",
    "branch_guard_explained": false,
    "return_target_trust": "suspicious",
    "root_cause_classification": "post_entry_branch_observed | exception_edge_before_branch | return_target_schema_gap | instrumentation_gap | hook_surface_unresolved",
    "next_bounded_action": "..."
  },
  "candidate_generation_changed": false,
  "ranking_changed": false,
  "search_budget_changed": false,
  "beam_budget_topn_timeout_frontier_limit_expanded": false,
  "breakpoint_probe_allowed": false
}
```

### 6.4 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_post_entry_step_runtime_audit
artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
current_state.latest_compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.stage=compare_handoff_post_entry_step_runtime_audit
```

不得删除或重命名旧字段。不得把当前 candidate、artifact path、runtime metric 写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "post_entry_step or hook_surface_repair or branch_operand_runtime or handoff_edge_operand"
python -m pytest -q tests\test_project_state.py -k "post_entry_step or hook_surface_repair or branch_operand_runtime or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果 Olly/runtime 环境不可用，仍必须：

```text
1. 生成 blocked artifact，说明 missing_environment 或 runtime_unavailable。
2. 不伪造 post_entry_events。
3. 不把 runtime_sidecar_executed 写成 true。
4. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

建议补充完整相关测试：

```text
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m pytest -q tests\test_project_state.py
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_post_entry_step_runtime_audit
round_id=round_20260601_post_entry_step_runtime_audit
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。不得把失败 lint 或 pending post-archive check 写成 PASSED。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. artifact_index.latest_artifacts_v2 中 compare_handoff_hook_surface_repair_audit 不是 current。
2. 3 个固定候选无法全部复现或被替换。
3. 需要新增候选、扩大 beam/topN/budget/timeout/frontier_limit 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
5. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
7. sidecar 无法捕获 post-entry branch/flags/next EIP；此时输出 instrumentation_gap 或 hook_surface_unresolved 并停止。
8. Olly/runtime 环境不可用；此时输出 BLOCKED artifact 并停止。
9. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

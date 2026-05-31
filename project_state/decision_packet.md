```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_bounded_handoff_exit_classifier_probe",
  "round_id": "round_20260531_bounded_handoff_exit_classifier_probe",
  "based_on_state_build_id": "state_20260527_153028_1d6dd81ecbd6",
  "based_on_state_digest": "1d6dd81ecbd615598f7b0fda09f1e859a4cba6a0d28b45711434e174ba6b5e02",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**。上一轮 `REWORK_REQUIRED` 已返工完成，artifact readability gap 已通过 Codex 本地文件系统检查闭合，但 GitHub 侧仍不能直接读取 `solve_reports/` 下 runtime artifacts。因此本轮可以基于 Codex 本地 current artifacts 继续推进，但报告必须继续区分：

```text
artifact_index.freshness=current != GitHub 可复核 artifact 内容
artifact_file_readable=true == Codex 本地工作树可读
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 仍只是状态派生建议，不得覆盖本 decision。

## 1. Goal

新增一个 **bounded handoff-exit classifier runtime sidecar**，用当前固定 3 个候选，不扩大搜索，不换候选池，专门回答：

```text
候选路径在 predecessor_handoff_call / handoff_helper_entry / process_exception 之后，
为什么没有到达 actual compare？
```

本轮目标不是求出最终 flag，也不是做 Base64/RC4 material capture，而是把当前模糊结论：

```text
decrypt_handler_entered_but_candidate_path_exits_before_handoff
```

细化为以下之一：

```text
1. branch_guard_before_compare
2. exception_unwind_before_compare
3. wrong_successor_or_hook_site
4. candidate_dependent_non_reaching_path
5. instrumentation_inconclusive
```

产出新的 artifact，例如：

```text
compare_handoff_exit_classifier_audit.json
```

并更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

必要时可以更新：

```text
project_state/artifact_index.json
project_state/current_state.json
```

但只允许 additive / current-run provenance 更新，不得删除旧字段。

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

当前 `task_packet.task` / `derived_task` 仍是：

```text
Diagnose bounded compare hook path reachability
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前关键 artifact 状态：

```text
run_manifest: current, Codex local readable
summary: current, Codex local readable
compare_hook_path_reachability_audit: current, Codex local readable
compare_real_lhs_provenance_audit: current, Codex local readable
```

上一轮 diagnosis 保留的核心证据：

```text
1. 3 个固定候选均 runtime-backed。
2. predecessor_handoff_call=1。
3. handoff_helper_entry=1。
4. process_exception=1。
5. actual_compare.observed_count=0。
6. actual_compare.entry_status=rejected。
7. 当前最小解释是 candidate-dependent exit or exception before compare。
```

当前 3 个固定候选必须保持不变：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前仍禁止把 fallback compare args 当作 provenance：

```text
compare_probe_fallback_is_provenance=false
old [ebp-0x1170] must not be reused as real LHS source
```

## 3. Do Not Do

严禁：

```text
1. 不回旧 sample_solver 盲搜。
2. 不扩大 beam / topN / budget / timeout。
3. 不新增候选池。
4. 不重复 exact2 basin value-pool evaluation。
5. 不重复 H1/H3 fixed boundary contrast set。
6. 不重复 current 5-candidate transform trace consistency audit。
7. 不运行 Base64/RC4 breakpoint probe。
8. 不做 Base64/RC4 material capture。
9. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非本轮 classifier 产生新的 instruction-level semantic evidence。
10. 不复用旧 [ebp-0x1170] 作为 real LHS source。
11. 不读取完整 solve_reports/。
12. 不读取完整 PROJECT_PROGRESS_LOG.txt。
13. 不修改 .codex-skills/。
14. 不修改 sample_corpus/reverse/。
15. 不提交完整 solve_reports/。
16. 不继续 corpus static audit 工程支线。
17. 不新增 rc4enc 静态分析报告。
```

本轮允许 runtime，但只能是：

```text
bounded handoff-exit classifier sidecar
same 3 candidates
same selected/current run context
only predecessor/handoff/exception/compare-successor surface
```

不得手工随意执行 sample.exe；如需执行，必须通过项目已有 harness/sidecar 机制，并在 report 中记录命令、候选数量、timeout、artifact path。

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
project_state/samplereverse_handoff_exit_diagnosis.md
```

必须有界读取：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

允许检查和修改：

```text
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
project_state/current_state.json
project_state/artifact_index.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不修改：

```text
reverse_agent/profiles/samplereverse.py
reverse_agent/harness.py
reverse_agent/sample_solver.py
```

除非发现 sidecar 注册必须改动对应 profile/harness glue，且必须在 report 中解释为什么无法只在 strategy 层实现。

不得修改：

```text
.codex-skills/
sample_corpus/reverse/
PROJECT_PROGRESS_LOG.txt
完整 solve_reports/
rc4enc_static_analysis_report.md
```

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. 当前 mainline 是否为 reverse_solving。
2. task_packet.task / derived_task 是否只是派生任务。
3. decision_packet.md 是否控制当前轮。
4. skill_profiles 是否为 reverse-agent-iteration@v2 + samplereverse-frontier@v2。
5. 四个 current artifacts 是否仍为 artifact_index current。
6. 四个 current artifacts 是否在 Codex 本地可读。
7. 是否没有读取完整 solve_reports/。
8. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
9. 是否没有修改 .codex-skills/。
10. 是否没有修改 sample_corpus/reverse/。
11. 是否没有回旧 sample_solver。
12. 是否没有扩大 beam/topN/budget/timeout。
13. 是否没有运行 Base64/RC4 breakpoint probe。
14. 是否没有复用旧 [ebp-0x1170] 作为 real LHS source。
15. 是否保持同 3 个固定候选。
16. classifier 是否输出每个候选的 control-flow outcome。
17. classifier 是否区分 branch_guard / exception_unwind / wrong_successor_or_hook_site / candidate_dependent_non_reaching_path / instrumentation_inconclusive。
18. classifier 是否记录 hook hit order 或等价的事件序列。
19. classifier 是否记录 process_exception 前后的最近事件。
20. classifier 是否记录 first possible compare successor 是否命中。
21. classifier 是否写出 artifact path、schema、candidate_count、runtime-backed count。
22. artifact_index 是否 additive 更新，不删除旧字段。
23. current_state 是否只更新当前瓶颈/最新 artifact 摘要，不写入 skill。
24. negative_results 是否未被重复违反。
25. lint-decision 是否通过。
26. lint-report 是否通过。
27. 相关 pytest 是否通过。
28. git diff --check 是否通过。
```

## 6. Implementation Scope

### 6.1 新增 bounded classifier sidecar

建议命名：

```text
compare_handoff_exit_classifier_audit
```

建议 artifact：

```text
compare_handoff_exit_classifier_audit.json
```

最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "candidate_count": 3,
  "candidates": [
    {
      "candidate_hex": "...",
      "runtime_backed": true,
      "events": [
        {
          "name": "predecessor_handoff_call",
          "hit_count": 1,
          "order": 1
        }
      ],
      "classification": "exception_unwind_before_compare",
      "classification_reason": "...",
      "actual_compare_observed": false,
      "process_exception_observed": true,
      "first_compare_successor_observed": false
    }
  ],
  "overall_classification": "exception_unwind_before_compare",
  "next_bounded_action": "..."
}
```

### 6.2 Hook / event surface

只能围绕当前已知 surface：

```text
predecessor_handoff_call
handoff_helper_entry
process_exception
first possible compare successor
actual_compare entry
```

不要新增 Base64/RC4 material hooks。

如果需要静态确认 first possible compare successor 的地址，只允许从 current artifacts 或 strategy 内已有常量/脚本生成逻辑中提取；不得全量反汇编或读取完整 solve_reports。

### 6.3 分类规则

建议规则：

```text
actual_compare_observed=true
=> compare_reached

process_exception_observed=true AND actual_compare_observed=false AND no compare successor observed
=> exception_unwind_before_compare

handoff_helper_entry=true AND successor/compare not reached AND no exception event
=> branch_guard_before_compare OR candidate_dependent_non_reaching_path

predecessor_handoff_call=true BUT handoff_helper_entry=false
=> wrong_successor_or_hook_site OR branch_before_helper

events insufficient / timeout / hook health bad
=> instrumentation_inconclusive
```

如果三个候选分类不同，不能强行合并；必须输出 per-candidate classification 和 overall classification。

### 6.4 Project state 更新

如果 sidecar 成功生成 artifact：

```text
artifact_index.latest_artifacts_v2.compare_handoff_exit_classifier_audit = current
current_state.latest_compare_handoff_exit_classifier_audit = summary
current_state.current_bottleneck.stage = compare_handoff_exit_classifier_audit
```

如果分类明确为 `exception_unwind_before_compare`，下一轮建议应聚焦 exception unwind edge，而不是搜索扩展。

如果分类明确为 `branch_guard_before_compare`，下一轮建议应聚焦 branch condition / guard operand provenance。

如果分类是 `wrong_successor_or_hook_site`，下一轮建议应先修正 hook surface，不得直接进入 material capture。

如果分类是 `instrumentation_inconclusive`，下一轮应修 instrumentation，不得扩大候选搜索。

## 7. Tests

必须运行：

```text
python -m pytest -q tests/test_compare_aware_search_strategy.py
python -m pytest -q tests/test_project_state.py
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果修改了其他 Python 文件，必须运行对应测试。

如果实际运行了 bounded runtime sidecar，必须在 report 中记录：

```text
1. exact command
2. candidate_count
3. timeout/budget
4. generated artifact path
5. runtime result status
6. whether sample.exe was executed only through bounded harness/sidecar
```

`pytest_result.txt` 顶部必须包含：

```json pytest_result_summary
{
  "schema_version": 1,
  "decision_id": "decision_20260531_bounded_handoff_exit_classifier_probe",
  "report_id": "<actual_report_id>",
  "round_id": "round_20260531_bounded_handoff_exit_classifier_probe",
  "status": "PASSED_or_FAILED_or_BLOCKED",
  "tests_ran": []
}
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED` 的条件：

```text
1. 四个 current artifacts 任一在 Codex 本地不可读。
2. 无法确认 3 个固定候选。
3. 需要扩大候选、beam、topN、budget、timeout 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 才能继续。
5. 需要读取完整 solve_reports/ 才能定位 hook surface。
6. 新 sidecar 无法在 bounded surface 内实现。
7. classifier 输出缺少 per-candidate classification。
8. lint-decision 或 lint-report 失败且不能通过只修 project_state/report 修复。
```

如果停止，报告必须给出最小下一步，不得泛泛写“继续完善”。

验收标准：

```text
ACCEPTED:
- decision/report/pytest_result ID 对齐。
- 只使用 3 个固定候选。
- 生成 compare_handoff_exit_classifier_audit.json 或等价 artifact。
- 每个候选都有 control-flow classification。
- 没有扩大搜索，没有 Base64/RC4 probe，没有旧 sample_solver。
- artifact_index/current_state additive 更新正确。
- pytest/lint/git diff --check 全部通过。

ACCEPTED_WITH_LIMITATIONS:
- classifier artifact 生成，但分类为 instrumentation_inconclusive，且原因清楚。
- 或 GitHub 侧无法复核 runtime artifact，但 Codex 本地路径、size、schema 已记录。

REWORK_REQUIRED:
- artifact/report 缺字段。
- 未区分 per-candidate classification。
- 把 stale/missing artifact 当 current。
- 重复 negative_results 已禁止方向。
- report 与 decision id 不匹配。

BLOCKED:
- current artifacts 本地不可读。
- 必须重建 project_state 或 bounded artifact 才能继续。
```

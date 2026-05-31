```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260531_resume_samplereverse_handoff_exit_diagnosis",
  "round_id": "round_20260531_resume_samplereverse_handoff_exit_diagnosis",
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

本轮正式从 corpus/static-audit 工程支线切回 **samplereverse 逆向解题主线**。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能自动覆盖本 decision。

本轮目标不是继续 corpus 工程，也不是重新盲搜，而是基于当前 `project_state` 中已经标记为 current 的 samplereverse artifacts，恢复解题上下文并做一次 **bounded no-runtime handoff-exit diagnosis**：解释为什么 candidate path 已进入 decrypt handler，但在 handoff / compare 连接之前退出，并给出下一轮最小可执行修复或探针计划。

## 1. Goal

恢复 `samplereverse` 解题主线，围绕当前瓶颈做有界诊断：

```text
current_bottleneck.stage = compare_hook_path_reachability_audit
current_bottleneck.reason = decrypt_handler_entered_but_candidate_path_exits_before_handoff
```

本轮只允许使用当前 project_state 与 current artifacts 做诊断，不运行新 runtime probe。

产出：

```text
project_state/samplereverse_handoff_exit_diagnosis.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

`samplereverse_handoff_exit_diagnosis.md` 必须回答：

```text
1. 当前 selected/current run 是什么。
2. 哪些 artifact 是 current，哪些是 stale/missing。
3. compare_hook_path_reachability_audit 说明了什么。
4. compare_real_lhs_provenance_audit 说明了什么。
5. 当前 handoff 前退出最可能是哪类原因：branch guard、exception unwind、wrong hook site、candidate-dependent path not reaching handoff、or unknown。
6. 当前证据是否足够生成下一轮具体 runtime probe。
7. 如果证据不足，是否需要先重建 project_state，而不是运行 probe。
8. 下一轮最小行动建议，必须避免 negative_results 中已失败方向。
```

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

当前 `task_packet.json` 中仍有旧 derived task：

```text
Diagnose bounded compare hook path reachability
```

但它不是执行权威；本 decision 才是当前轮执行权威。

当前 project_state 中的关键状态：

```text
current_bottleneck.stage = compare_hook_path_reachability_audit
current_bottleneck.blocker = decrypt_handler_entered_but_candidate_path_exits_before_handoff
current_bottleneck.confidence = medium
```

当前 known transform 仍为：

```text
input -> UTF-16LE -> Base64 -> RC4 -> compare flag{ prefix
```

当前 best/frontier 候选仍来自旧 project_state：

```text
exact2: 78d540b49c59077041414141414141, runtime_ci_exact_wchars=2, runtime_ci_distance5=246
frontier/exact1: 5a3e7f46ddd474d041414141414141, runtime_ci_exact_wchars=1, runtime_ci_distance5=258
```

artifact freshness 约束：

```text
1. latest_artifacts_v2.compare_hook_path_reachability_audit is current.
2. latest_artifacts_v2.compare_real_lhs_provenance_audit is current.
3. latest_artifacts_v2.run_manifest is current.
4. latest_artifacts_v2.summary is current.
5. base64_rc4_static_point_discovery / compare_probe / function_semantic_audit / compare_handoff_return_site_probe 等旧 tool_artifacts 多数是 stale，只能作为历史背景，不能作为当前证据。
6. missing artifacts 不能当作证据。
```

当前可用 current artifact 路径来自 `project_state/artifact_index.json`：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

如果上述路径不存在或无法读取，不要读取完整 `solve_reports/`，而是报告 `BLOCKED` 并建议重新执行：

```text
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
```

## 3. Do Not Do

严禁：

```text
1. 不运行任何 sample.exe。
2. 不运行 samplereverse harness。
3. 不运行 runtime probe。
4. 不运行 Base64/RC4 breakpoint probe。
5. 不运行 pywinauto / GUI validation。
6. 不运行 IDA / OllyDbg / Frida。
7. 不回旧 sample_solver 盲搜。
8. 不扩大 beam / topN / budget / timeout。
9. 不重复 exact2 basin value-pool evaluation。
10. 不重复 H1/H3 fixed boundary contrast set。
11. 不重复 current 5-candidate transform trace consistency audit。
12. 不重复 compare return-site audit without using classification。
13. 不重复 producer material confirmation without instruction-level evidence。
14. 不把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当作 Base64/RC4 material producer，除非有新语义证据。
15. 不复用旧 [ebp-0x1170] 作为 real LHS source，除非有 provenance evidence。
16. 不读取完整 solve_reports/。
17. 不读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不修改 .codex-skills/。
19. 不推进 corpus static audit 支线。
20. 不修改 sample_corpus/reverse/。
```

特别限制：

```text
1. 本轮是 no-runtime diagnosis，只允许读取 project_state 和有界 current artifacts。
2. 如果必须运行新 probe 才能回答问题，停止并在 diagnosis 中给出下一轮最小 probe 设计，不要直接执行。
3. 不得把 stale/missing artifact 当作 current evidence。
4. 不得仅因为 task_packet 仍是旧 derived_task 就跳过本 decision。
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
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_hook_path_reachability_audit/compare_hook_path_reachability_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

允许检查源码，只读为主：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

允许新增或修改：

```text
project_state/samplereverse_handoff_exit_diagnosis.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

原则上不修改代码。如果 Codex 发现 project_state lint/report 小问题需要最小修复，只能修改 project_state 报告文件，不得改 runtime/harness/strategy 代码。

不得修改：

```text
.codex-skills/
reverse_agent/strategies/compare_aware_search.py
reverse_agent/profiles/samplereverse.py
reverse_agent/sample_solver.py
reverse_agent/harness.py
sample_corpus/reverse/
solve_reports/
```

## 5. Required Audit

Codex 报告必须逐项回答：

```text
1. 当前 mainline 是否已切回 reverse_solving。
2. task_packet.task 是否只是 derived_task，而不是当前执行权威。
3. decision_packet.md 是否控制当前轮。
4. 当前 skill_profiles 是否为 reverse-agent-iteration@v2 + samplereverse-frontier@v2。
5. compare_hook_path_reachability_audit 是否为 current。
6. compare_real_lhs_provenance_audit 是否为 current。
7. run_manifest / summary 是否为 current。
8. 是否没有把 stale/missing artifact 当作 current evidence。
9. compare_hook_path_reachability_audit 的核心结论是什么。
10. compare_real_lhs_provenance_audit 的核心结论是什么。
11. handoff 前退出的最小解释是什么。
12. 现在是否足以设计下一轮 bounded runtime probe。
13. 如果不足，是否需要先 project_state build 或补 artifact index。
14. 是否没有运行 sample.exe。
15. 是否没有运行 runtime probe。
16. 是否没有运行 Base64/RC4 breakpoint probe。
17. 是否没有读取完整 solve_reports/。
18. 是否没有读取完整 PROJECT_PROGRESS_LOG.txt。
19. 是否没有修改 .codex-skills/。
20. 是否没有修改 sample_corpus/reverse/。
21. 是否没有回旧 sample_solver 或扩大搜索预算。
22. 是否没有重复 negative_results 中已失败方向。
```

## 6. Implementation Scope

### 6.1 生成 diagnosis 文档

新增：

```text
project_state/samplereverse_handoff_exit_diagnosis.md
```

必须包含：

```text
1. Decision / round metadata 摘要。
2. State source 摘要：state_build_id、digest、selected/current run。
3. Artifact freshness table：current / stale / missing。
4. Current evidence：逐项总结 current artifacts。
5. Handoff-exit hypothesis：列出 2-4 个候选原因，并按证据强弱排序。
6. Negative-results compliance：说明没有重复哪些已失败方向。
7. Next action recommendation：给出下一轮最小行动。
8. Stop condition：如果证据不足，明确要求 project_state build 或 bounded artifact rebuild，而不是 runtime probe。
```

### 6.2 不实现新 solver

本轮不得实现：

```text
1. DES / RC4 / Base64 solver。
2. new guided pool search。
3. new candidate beam expansion。
4. new runtime hook / breakpoint probe。
5. sample_solver fallback。
```

### 6.3 不修改运行逻辑

本轮不得修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/harness.py
reverse_agent/profiles/samplereverse.py
```

如果 Codex 认为必须修改代码才能继续，停止并在 diagnosis 中提出下一轮 code-change decision，不要直接改。

### 6.4 更新 Codex report

更新：

```text
project_state/codex_execution_report.md
```

顶部必须为：

```text
```json codex_report_summary
```

字段必须包含：

```text
schema_version
report_id = report_20260531_resume_samplereverse_handoff_exit_diagnosis
round_id = round_20260531_resume_samplereverse_handoff_exit_diagnosis
based_on_decision_id = decision_20260531_resume_samplereverse_handoff_exit_diagnosis
status
acceptance_recommendation
files_changed
tests_ran
generated_artifacts
```

### 6.5 更新 pytest_result.txt

即使本轮不改代码，也必须记录最小检查命令：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果没有运行 pytest，`pytest_result.txt` 中必须明确写：

```text
No pytest required: documentation/project_state diagnosis only; no code changed.
```

## 7. Tests

必须运行：

```text
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

不要求运行：

```text
python -m pytest -q
```

除非 Codex 修改了代码。若修改代码，则必须运行相关测试，并在 report 中解释为什么违反了“原则上不修改代码”的默认限制。

不得运行：

```text
任何 sample.exe
samplereverse harness
IDA / OllyDbg / Frida / pywinauto
runtime probe
Base64/RC4 breakpoint probe
old sample_solver blind search
```

## 8. Stop Conditions

立即停止并报告 `BLOCKED`：

```text
1. current artifact 路径不存在或无法读取。
2. artifact_index 与实际文件冲突，无法判断 current evidence。
3. 必须读取完整 solve_reports/ 才能继续。
4. 必须运行 runtime probe 才能回答当前问题。
5. 必须修改 compare_aware_search.py / harness.py / samplereverse.py 才能继续。
6. 必须修改 .codex-skills/。
7. lint-decision 或 lint-report 无法通过。
```

完成条件：

```text
1. project_state/samplereverse_handoff_exit_diagnosis.md 已生成。
2. diagnosis 只基于 project_state 和 bounded current artifacts。
3. diagnosis 明确 artifact freshness，不把 stale/missing 当 current。
4. diagnosis 明确 handoff 前退出的最小解释。
5. diagnosis 给出下一轮最小行动建议。
6. codex_execution_report.md 与本 decision 对齐。
7. pytest_result.txt 记录 lint-decision / lint-report / git diff --check。
8. 未执行任何 sample.exe。
9. 未运行 runtime probe。
10. 未读取完整 solve_reports/。
11. 未修改 .codex-skills/。
12. 未修改 samplereverse runtime/strategy 代码。
```
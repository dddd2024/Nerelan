```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_post_entry_instrumentation_rework",
  "round_id": "round_20260601_post_entry_instrumentation_rework",
  "based_on_state_build_id": "state_20260601_094922_a9e79b27f71f",
  "based_on_state_digest": "a9e79b27f71f1cbd4466a311e25b8efb41500ec3da6ca428994e534594d910fc",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但任务不是继续求解、不是扩大搜索、不是 Base64/RC4 probe。本轮只修复 `compare_handoff_post_entry_step_runtime_audit` 的 runtime instrumentation，使 post-entry 单步观测从当前的 `runtime_unavailable / instrumentation_gap` 推进到可解释的 bounded runtime 结果，或者输出更精确的环境阻塞原因。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

修复或界定 `compare_handoff_post_entry_step_audit.py` 的有界 runtime 执行能力，生成更新后的 artifact：

```text
compare_handoff_post_entry_step_runtime_audit.json
```

核心目标：

```text
把当前 runtime_unavailable 精化为以下之一：
1. post_entry_breakpoint_observed
2. post_entry_single_step_observed
3. debugger_backend_missing
4. target_process_launch_failed
5. breakpoint_install_failed
6. step_api_unavailable
7. instrumentation_gap_but_environment_verified
```

本轮必须回答：

```text
1. 当前 sidecar 为什么 runtime_sidecar_executed=false。
2. 是缺 Olly/Frida/debugger backend，还是 sidecar 参数、进程启动、断点地址、单步 API、日志解析、artifact 写入链路出错。
3. 0x2338 predecessor_handoff_call 和 0x1b50 handoff_helper_entry 的 breakpoint 是否至少能被安装或验证。
4. 如果不能执行 sample，是否能生成明确的 environment_diagnostic artifact，而不是笼统 runtime_unavailable。
5. 如果能执行，是否能对 3 个固定候选捕获 handoff_helper_entry 后有限步 EIP / instruction / EFLAGS / next_eip。
6. 若仍不能捕获，不得扩大范围；必须给出最小阻塞原因和下一步 bounded action。
```

本轮不是求最终 flag，不新增候选，不运行 Base64/RC4 breakpoint probe，不做 material capture，不做 crypto hook。

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

当前 state：

```text
state_build_id=state_20260601_094922_a9e79b27f71f
state_digest=a9e79b27f71f1cbd4466a311e25b8efb41500ec3da6ca428994e534594d910fc
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Repair bounded post-entry step instrumentation
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 bottleneck：

```text
stage=compare_handoff_post_entry_step_runtime_audit
blocker=runtime_unavailable
reason=runtime_unavailable
confidence=medium
```

current artifact：

```text
compare_handoff_post_entry_step_runtime_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_post_entry_step_runtime_audit\compare_handoff_post_entry_step_runtime_audit.json
  sha256=83f18730fa05fd88b4bc82c7e8dad53198ddc7d0f3421c5796ef01366f5d71c6
```

当前 artifact 结论：

```text
classification=runtime_unavailable
overall_classification=runtime_unavailable
runtime_sidecar_executed=false
branch_guard_explained=false
first_divergence_point=""
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
max_steps_per_candidate=32
next_bounded_action=narrower_post_entry_breakpoint
```

已知固定候选必须保持不变：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前关键限制：

```text
1. post_entry_events 为空。
2. branch_eip / instruction / eflags / condition / next_eip 仍为空。
3. return_target_observation.trust=instrumentation_gap。
4. 当前不能把 runtime_unavailable 当作逆向语义证据。
5. Base64/RC4 breakpoint probe 仍被 negative_results 阻断。
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
9. 不把 post-entry instrumentation rework 变成 material probe。
10. 不重复生成同样的 runtime_unavailable artifact 而不增加诊断字段。
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
2. 只允许验证 debugger/backend、target launch、breakpoint install、single-step API、artifact parse/write。
3. 若 runtime 可用，只允许 control-flow surface：EIP、instruction/disasm、EFLAGS、branch condition/outcome、next EIP、process_exception、compare successor、actual compare。
4. 单候选最大 step 数仍必须有硬上限，max_steps <= 32。
5. 不允许 dump 任意大内存，不允许保存 material bytes，不允许输出 candidate score/ranking。
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
project_state.artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
project_state.current_state.latest_compare_handoff_post_entry_step_runtime_audit
project_state.current_state.current_bottleneck
project_state/rounds/round_20260601_post_entry_step_runtime_audit/round_manifest.json
```

允许有界读取上游 current artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_hook_surface_repair_audit/compare_handoff_hook_surface_repair_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_branch_operand_runtime_audit/compare_handoff_branch_operand_runtime_audit.json
```

允许检查和修改：

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
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
6. compare_handoff_post_entry_step_runtime_audit freshness 是否为 current。
7. 是否保持同 3 个固定候选。
8. 是否没有新增候选、扩大 beam/topN/budget/timeout/frontier_limit。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/、sample_corpus/reverse/、harness.py、sample_solver.py。
13. 是否定位 runtime_sidecar_executed=false 的直接原因。
14. 是否区分 debugger_backend_missing / target_process_launch_failed / breakpoint_install_failed / step_api_unavailable / artifact_parse_error。
15. 是否验证 0x2338 和 0x1b50 breakpoint 是否可安装或可命中。
16. 若 runtime 可用，是否只捕获有限 control-flow surface。
17. 若 runtime 不可用，是否生成更精确 blocked artifact，而不是重复笼统 runtime_unavailable。
18. artifact 是否包含 environment_diagnostics。
19. artifact 是否包含 breakpoint_installation_diagnostics。
20. artifact 是否包含 sidecar_invocation_diagnostics。
21. artifact 是否明确 breakpoint_probe_allowed=false。
22. artifact_index 是否 additive 更新，不删除旧字段。
23. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
24. negative_results 是否未被重复违反。
25. lint-decision 是否通过；若执行后 state rebuild 导致 digest mismatch，必须标记 PARTIAL/NEEDS_REVIEW，不得写 SUCCESS/ACCEPTED。
26. lint-report 是否通过。
27. 相关 pytest 是否通过。
28. git diff --check 是否通过。
29. pytest_result.txt 是否与真实命令结果一致。
30. codex_report_summary 是否与当前 decision_id 匹配。
31. 是否归档本轮 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 Instrumentation diagnostics first

先增强 `compare_handoff_post_entry_step_audit.py` 的诊断输出，而不是扩大 runtime 行为。

必须新增或确认这些诊断字段：

```json
{
  "environment_diagnostics": {
    "platform": "",
    "python_executable": "",
    "debugger_backend": "olly | frida | unavailable | unknown",
    "backend_import_ok": false,
    "backend_error": "",
    "target_executable_exists": false,
    "target_launch_attempted": false,
    "target_launch_ok": false,
    "target_launch_error": ""
  },
  "breakpoint_installation_diagnostics": {
    "predecessor_handoff_call": {
      "address": "0x2338",
      "install_attempted": false,
      "install_ok": false,
      "hit": false,
      "error": ""
    },
    "handoff_helper_entry": {
      "address": "0x1b50",
      "install_attempted": false,
      "install_ok": false,
      "hit": false,
      "error": ""
    }
  },
  "single_step_diagnostics": {
    "step_attempted": false,
    "step_api_available": false,
    "step_count": 0,
    "first_step_eip": "",
    "last_step_eip": "",
    "error": ""
  },
  "artifact_parse_diagnostics": {
    "raw_log_path": "",
    "raw_log_exists": false,
    "parse_attempted": false,
    "parse_ok": false,
    "parse_error": ""
  }
}
```

### 6.2 Narrower post-entry breakpoint

如果 full single-step API 不可用，允许新增更窄的 post-entry breakpoint 验证，但仍必须只限 control-flow surface：

```text
1. handoff_helper_entry + 1 instruction boundary
2. known post-entry candidate branch boundary if statically known
3. process_exception entry
4. compare successor / actual compare entry
```

禁止把 narrower breakpoint 扩展到 Base64/RC4 或 material buffer。

### 6.3 Strategy integration

`CompareAwareSearchStrategy` 的入口仍使用：

```text
compare_handoff_post_entry_step_runtime_audit
```

但本轮需要支持更精确的状态分类：

```text
runtime_unavailable
debugger_backend_missing
target_process_launch_failed
breakpoint_install_failed
entry_breakpoint_not_hit
step_api_unavailable
post_entry_breakpoint_observed
post_entry_single_step_observed
instrumentation_gap_but_environment_verified
```

### 6.4 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_post_entry_step_runtime_audit
artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
current_state.latest_compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.stage=compare_handoff_post_entry_step_runtime_audit
current_state.current_bottleneck.reason=<more specific classification>
```

不得删除或重命名旧字段。不得把动态事实写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "post_entry_step or instrumentation or hook_surface_repair"
python -m pytest -q tests\test_project_state.py -k "post_entry_step or instrumentation or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果 runtime 环境仍不可用，必须：

```text
1. 生成 blocked artifact。
2. 写明具体 unavailable 子类。
3. 不伪造 post_entry_events。
4. 不把 runtime_sidecar_executed 写成 true。
5. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_post_entry_instrumentation_rework
round_id=round_20260601_post_entry_instrumentation_rework
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. artifact_index.latest_artifacts_v2 中 compare_handoff_post_entry_step_runtime_audit 不是 current。
2. 3 个固定候选无法全部保留。
3. 需要新增候选、扩大 beam/topN/budget/timeout/frontier_limit 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
5. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
7. debugger backend 不存在或无法启动 target；此时输出 debugger_backend_missing / target_process_launch_failed 并停止。
8. breakpoint 无法安装或无法命中；此时输出 breakpoint_install_failed / entry_breakpoint_not_hit 并停止。
9. single-step API 不可用；此时输出 step_api_unavailable，并只允许建议下一轮 narrower_post_entry_breakpoint。
10. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

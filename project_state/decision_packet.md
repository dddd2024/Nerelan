```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_sidecar_hook_install_vs_compareprobe_divergence_20260521",
  "round_id": "round_20260521_samplereverse_sidecar_hook_install_vs_compareprobe_divergence",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 `decision_samplereverse_sidecar_no_hook_observation_root_cause_20260521` 的 Codex 报告是可信的 `PARTIAL / REWORK_REQUIRED`：它没有把失败伪装成成功，并把 sidecar 退化问题收窄为 `timeout_before_hook_install`。但核心问题仍未解决：`compare_pre_compare_handoff_target_probe.py` 这条 sidecar 路径没有 emit `hooks_installed`，`hook_count=0`，而 `compare_probe.py` 仍然能通过 fallback 捕获 diagnostic `0x258c` compare args。

本轮目标不是推进候选搜索，也不是恢复大范围 runtime probing，而是对比 sidecar 与 CompareProbe 的 Frida script load / hook install / invocation 差异，找到为什么 sidecar 无法确认 hook 安装。

## 1. Goal

本轮目标：

```text
1. 审计 compare_pre_compare_handoff_target_probe.py 为什么在 bounded sidecar run 中只写出 script_started，未 emit hooks_installed。
2. 审计 compare_probe.py 为什么仍能捕获 diagnostic compare args，明确它与 sidecar 在 spawn/attach/resume、script.load、module base/RVA 计算、hook point schema、message handling、timeout/stop condition、UI trigger 上的差异。
3. 修复或最小化改造 sidecar hook-install observability，使 artifact 至少能区分：script_load_failed、js_compile_error、module_not_found、hook_install_failed、hook_installed_but_target_not_reached、ui_trigger_failed。
4. 保持 two-candidate bounded scope；不新增候选，不扩大 beam/budget/topN/frontier iteration，不运行 Base64/RC4 breakpoint probe。
5. 如果能修复 hook install，重新运行 bounded sidecar，目标至少恢复到 helper/write-monitor 可观察状态；如果仍失败，report.status 必须是 PARTIAL 或 BLOCKED，不能写 SUCCESS。
```

最低可接受推进：

```text
A. 明确解释 sidecar 没有 hooks_installed 的根因，或给出 BLOCKED 且说明缺失日志/环境。
B. 明确解释 CompareProbe fallback 能捕获 compare args 而 sidecar 不能的差异点。
C. 新 artifact 必须包含 hook-install 层面的可执行证据，不得只重复 timeout_before_hook_install。
```

## 2. Current Evidence

当前任务主线：逆向解题主线，样本为 `samplereverse`。

当前 `task_packet.json` 是样本派生状态包，不是本轮 Codex 执行命令：

```text
task = Improve compare lhs last-writer instrumentation
derived_task = Improve compare lhs last-writer instrumentation
task_source = derived_from_sample_artifacts
profile = samplereverse
sample = samplereverse
execution_scope = decision_packet_controls_current_round
active_decision_packet = project_state/decision_packet.md
```

当前 Codex 执行权威来自本文件 `project_state/decision_packet.md`。

当前 live state：

```text
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
source_harness_run = sr_lhs_thread_follow_timing_20260520_r4
active_strategy = CompareAwareSearchStrategy
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.stage = compare_real_lhs_provenance_audit
```

当前 bounded candidates 固定为：

```text
candidate 1 / exact2:
  candidate_hex = 78d540b49c59077041414141414141
  runtime_ci_distance5 = 246
  runtime_ci_exact_wchars = 2
  compare_semantics_agree = true

candidate 2 / exact1-frontier:
  candidate_hex = 5a3e7f46ddd474d041414141414141
  runtime_ci_distance5 = 258
  runtime_ci_exact_wchars = 1
  compare_semantics_agree = true
```

当前 `compare_real_lhs_provenance_audit` 的关键事实：

```text
classification = compare_lhs_runtime_backed_writer_missing
0x258c compare 已确认
arg0 = candidate-dependent real LHS
arg1 = flag side
old [ebp-0x1170] frame anchor rejected
last_writer_candidates = []
runtime_backed_count = 0
Base64/RC4 breakpoint probe remains blocked
```

上一轮 GPT 审计结论：

```text
ACCEPTED_WITH_LIMITATIONS

原因：
1. decision/report 绑定正确。
2. Codex 没有再把失败 runtime 标成 SUCCESS。
3. root cause 被收窄到 timeout_before_hook_install。
4. 测试、lint、archive 记录完整。
5. 没有再次写 PROJECT_PROGRESS_LOG.txt。
6. 没有违反 Base64/RC4 probe、旧 solver、扩大搜索等禁止方向。
7. 但核心 sidecar 仍未恢复 hook observation，也未解决 CompareProbe 与 sidecar 可观察性差异。
```

上一轮 runtime artifact 摘要：

```text
run_name = sr_lhs_last_writer_sidecar_no_hook_observation_root_cause_20260521_r1
classification = instrumentation_incomplete
instrumentation_failure_stage = timeout_before_hook_install
root_cause_hypothesis = timeout_before_hook_install
hook_install_status = not_confirmed
hook_count = 0
spawn_attach_resume_status = empty / not confirmed
ui_trigger_status = empty / not confirmed
helper_observation_count = 0
static_compare_observation_count = 0
same_process_compare_args_captured = false
diagnostic_compare_args_captured = true
compare_probe_fallback_used = true
compare_probe_fallback_is_provenance = false
write_monitor_health.observed_candidate_count = 2
write_monitor_health.followed_thread_count = 0
write_monitor_health.raw_write_count = 0
write_monitor_health.filtered_intersecting_write_count = 0
write_monitor_health.runtime_stages = [script_started]
project_progress_log_handling = untouched
```

需要对比的前序 sidecar run：

```text
sr_lhs_last_writer_sidecar_fix_20260521_r1:
  classification = instrumentation_incomplete
  instrumentation_failure_stage = same_process_compare_args_missing
  same_process_compare_args_captured = false
  diagnostic_compare_args_captured = true
  compare_probe_fallback_used = true
  compare_probe_fallback_is_provenance = false
  write_monitor_health.observed_candidate_count = 2
  write_monitor_health.followed_thread_count = 1
  write_monitor_health.raw_write_count = 323
  write_monitor_health.filtered_intersecting_write_count = 0
```

artifact freshness 现状：

```text
current in live artifact_index.latest_artifacts_v2:
  compare_probe
  compare_probe_log
  compare_real_lhs_provenance_audit
  run_manifest
  summary

not in live artifact_index.latest_artifacts_v2:
  sr_lhs_last_writer_sidecar_fix_20260521_r1 compare_lhs_last_writer_provenance_audit
  sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1 compare_lhs_last_writer_provenance_audit
  sr_lhs_last_writer_sidecar_no_hook_observation_root_cause_20260521_r1 compare_lhs_last_writer_provenance_audit
```

sidecar artifacts 可从本地路径有界读取，但不得当作 live indexed current artifact。

## 3. Do Not Do

不要做以下事情：

```text
不要运行 Base64/RC4 breakpoint probe。
不要回旧 sample_solver。
不要扩大 beam、topN、budget、timeout、frontier iteration 作为推进方式。
不要新增候选。
不要使用 compare_semantics_agree=false candidates 作为主线。
不要重复 exact2 basin value-pool evaluation。
不要重复 H1/H3 fixed boundary contrast set。
不要重复当前 5-candidate transform trace consistency audit，除非新增 runtime evidence。
不要把 CompareProbe fallback 当作 provenance。
不要跨进程、跨 run、跨 candidate 强行合并 compare arg0 地址和 write_ring 事件。
不要复用旧 [ebp-0x1170] 作为真实 LHS 来源。
不要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要继续写 PROJECT_PROGRESS_LOG.txt。
不要继续 harness Phase 3 hardening。
不要修改 docs/phase2_harness_reproducibility_completion.md。
不要引入重型依赖或通用 agent runtime。
不要把 live artifact_index 里 missing/stale 的 sidecar artifact 当成 current evidence。
```

## 4. Files To Inspect

必须审计：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/decision_packet.md
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/rounds/round_20260521_samplereverse_sidecar_no_hook_observation_root_cause/round_manifest.json
project_state/rounds/round_20260521_samplereverse_sidecar_no_hook_observation_root_cause/git_diff.patch
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/compare_probe.py
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
```

必须有界读取 current artifacts：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.log
```

允许有界读取 sidecar artifacts/logs：

```text
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*

solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*

solve_reports/harness_runs/sr_lhs_last_writer_sidecar_no_hook_observation_root_cause_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_no_hook_observation_root_cause_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_no_hook_observation_root_cause_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*
```

如果上述 artifact/log 本地不存在，不要扫描完整 `solve_reports/`；报告 `BLOCKED`，或者重新运行 bounded sidecar 并说明缺失路径。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 为什么上一轮只能 ACCEPTED_WITH_LIMITATIONS，而不是 ACCEPTED。
3. sidecar 的 `timeout_before_hook_install` 是从哪些 artifact/log 字段推导出来的。
4. compare_pre_compare_handoff_target_probe.py 的 Frida script lifecycle：spawn -> attach -> create_script -> script.on -> script.load -> hooks_installed send -> resume -> UI trigger。
5. compare_probe.py 的等价 lifecycle，逐项对比 sidecar 差异。
6. 两者是否使用相同 target path、module base 获取方法、RVA/module_offset 解析、hook point 数组 schema。
7. sidecar JS 是否存在编译/语法错误、异常被吞掉、send stage message 在 script.load 前失败、或 script_errors 未进入 artifact 的情况。
8. sidecar 是否因为 Path(sys.argv[0]).stem / wrapper entrypoint / direct execution 造成 artifact kind、cwd、relative path、args 或 timeout 行为差异。
9. sidecar 是否在 script.load 前写 initial payload 后 subprocess 被 timeout 杀死，导致 hooks_installed 未发送。
10. CompareProbe fallback 为什么能捕获 diagnostic compare args；是否因为它用不同 wait condition、不同 hook address、不同 UI trigger、不同 process lifetime。
11. 是否能用最小 dry-run/hook-install check 在不扩大候选的情况下确认 sidecar JS hook install。
12. 本轮是否需要重建 project_state；如需要只能运行 project_state build/status，不得手动编辑 state JSON。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有确认为必要时，才允许小幅修改：

```text
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/olly_scripts/compare_probe.py
```

修改目的只能是：

```text
1. 增加 sidecar hook-install observability。
2. 暴露 JS compile/load/hook-install errors。
3. 对齐 CompareProbe 与 sidecar 的 hook schema 或 module base/RVA conversion。
4. 增加 bounded dry-run/hook-install check。
5. 复用 compare_probe 的已验证 hook install/capture 逻辑，但不得改变 CompareProbe 既有输出语义。
```

允许生成 runtime artifact，但不要提交完整 solve_reports：

```text
solve_reports/harness_runs/<run_name>/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
```

允许归档：

```text
project_state/rounds/round_20260521_samplereverse_sidecar_hook_install_vs_compareprobe_divergence/*
```

不要修改：

```text
PROJECT_PROGRESS_LOG.txt
reverse_agent/harness.py
reverse_agent/project_state.py
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/schema.md
docs/phase2_harness_reproducibility_completion.md
```

如确需刷新 project_state，只能运行：

```powershell
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
```

并在 report 中说明原因。

### 6.1 Required sidecar behavior

sidecar scope 必须保持 bounded：

```text
compare site: 0x258c
post_handoff_lhs_reload: 0x2559
bounded helper candidate: 0x1b50
candidate 1: 78d540b49c59077041414141414141
candidate 2: 5a3e7f46ddd474d041414141414141
```

必须做到以下之一：

```text
A. 修复 hook install observability：artifact 能确认 hooks_installed/hook_count，并继续解释是否到达 helper/static compare。
B. 恢复到 helper/write monitor 可观察状态，并解释为何还不到 0x258c。
C. 捕获 same-process 0x258c compare args，并进入 compare_reached_but_writer_missing 或 runtime_backed_last_writer_identified。
D. 若仍无法 hook install，classification/report 必须明确 BLOCKED 或 PARTIAL，并写出 script_load_failed/js_compile_error/module_not_found/hook_install_failed 等具体阶段。
```

如果使用 CompareProbe fallback：

```text
1. fallback 只能填充 diagnostic fields。
2. artifact 必须包含 compare_probe_fallback_is_provenance = false。
3. 不能把 fallback arg0 地址与另一进程/另一 run 的 write events 关联成 runtime-backed writer。
4. 必须对比说明为什么 fallback 可观察而 sidecar 不可观察。
```

### 6.2 Artifact output rules

新 artifact 必须包含：

```text
schema_version
artifact_kind = compare_lhs_last_writer_provenance_audit
sample
run_name
classification
compare_site = 0x258c
candidate_inputs_hex
candidate_input_hex
same_process_provenance: true/false
same_process_compare_args_captured: true/false
diagnostic_compare_args_captured: true/false
compare_probe_fallback_used: true/false
compare_probe_fallback_is_provenance: false when used
write_monitor_health
bounded_failures
instrumentation_failure_stage
root_cause_hypothesis
root_cause_evidence
hook_install_status
hook_count
requested_hook_count
script_load_status
script_load_error
frida_message_error_count
spawn_attach_resume_status
ui_trigger_status
helper_observation_count
static_compare_observation_count
candidate_log_paths
compare_probe_sidecar_diff
compared_prior_run
next_allowed_probe
base64_rc4_breakpoint_probe_run = false
candidate_generation_changed = false
beam_budget_topn_timeout_frontier_limit_expanded = false
project_progress_log_handling = untouched
```

如果没有确认 writer：

```text
bounded_failures 必须可执行，不得只写 unknown 或 generic timeout。
next_allowed_probe 必须仍然是 bounded hook-install / last-writer instrumentation 修复方向，不得跳到 Base64/RC4 probe。
```

## 7. Tests

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py reverse_agent\strategies\compare_aware_search.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "compare_lhs_last_writer or compare_real_lhs_last_writer or pre_compare_handoff"
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
```

如果修改 `compare_lhs_last_writer_provenance.py`，额外运行：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_lhs_last_writer_provenance.py
```

如果修改 `compare_probe.py`，额外运行：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_probe.py
```

如果 runtime 环境可用，必须重新跑 bounded sidecar，并记录：

```text
run_name
candidate_inputs_hex
scripted_hook_status
scripted_returncode
final_runtime_stage
hook_install_status
hook_count
requested_hook_count
script_load_status
script_load_error
frida_message_error_count
spawn_attach_resume_status
ui_trigger_status
helper_observation_count
static_compare_observation_count
same_process_compare_args_captured
followed_thread_count
raw_write_count
compare_probe_fallback_used
compare_probe_fallback_is_provenance=false
compare_probe_sidecar_diff
root_cause_hypothesis
root_cause_evidence
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260521_samplereverse_sidecar_hook_install_vs_compareprobe_divergence
```

注意：

```text
如果仍无法确认 hook install，report.status 必须是 PARTIAL 或 BLOCKED，不得是 SUCCESS。
如果关键 artifact/log 缺失导致无法判断，report.status 必须是 BLOCKED。
```

### 7.1 Required unit tests

新增或更新测试必须覆盖：

```text
1. no hooks_installed message maps to timeout_before_hook_install or script_load_failed with explicit root_cause_evidence。
2. JS compile/load error maps to script_load_failed or js_compile_error。
3. hook install error messages are counted and surfaced as hook_install_failed / partial_or_failed。
4. installed hooks but no helper/static observation maps to timeout_after_ui_trigger_before_helper or helper_hook_not_reached。
5. helper observed but static compare missing maps to helper_hook_reached_but_static_compare_missing。
6. static compare observed without args maps to argument_extraction_failed。
7. CompareProbe fallback cannot make runtime_backed_last_writer_identified。
8. same-process compare args + raw writes but no intersecting write maps to compare_reached_but_writer_missing。
9. candidate set remains exactly two bounded candidates unless an explicit test fixture overrides it。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 只能重复 timeout_before_hook_install，但不能新增 hook-install 层面的 evidence。
2. 无法读取必要 sidecar/CompareProbe logs，也无法重新运行 bounded sidecar。
3. 需要回旧 sample_solver。
4. 需要只靠扩大 beam/budget/topN/timeout 才能推进。
5. 需要在 real LHS writer/provenance 识别前运行 Base64/RC4 breakpoint probe。
6. 需要把 stale artifact 当作 current evidence。
7. 需要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
8. 需要读取或提交完整 solve_reports。
9. 需要使用 compare_semantics_agree=false candidate 作为主线。
10. 需要重复 negative_results 中已禁止的 exact2 basin 或 H1/H3 contrast 方向。
11. 需要把 CompareProbe fallback 当成 provenance。
12. 无法保证 compare args 与 write events 来自同一 process/thread，却仍想输出 runtime_backed_last_writer_identified。
13. 无法让 report.based_on_decision_id 绑定当前 decision_id。
14. 无法让 pytest_result.txt 记录真实测试和 runtime/blocked 状态。
15. 需要继续写 PROJECT_PROGRESS_LOG.txt。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary 存在，based_on_decision_id 指向 decision_samplereverse_sidecar_hook_install_vs_compareprobe_divergence_20260521。
2. 必须解释 sidecar 为什么没有 emit hooks_installed，或明确 BLOCKED。
3. 必须对比 CompareProbe fallback 与 sidecar 的可观察性差异。
4. 如果仍无法确认 hook install，report.status 不能是 SUCCESS。
5. 不破坏 PROJECT_PROGRESS_LOG.txt revert，且不再修改 PROJECT_PROGRESS_LOG.txt。
6. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
7. 没有运行 Base64/RC4 breakpoint probe。
8. 没有回旧 solver 或扩大搜索。
9. 保持两个 bounded candidates，不新增候选搜索。
10. artifact 明确区分 diagnostic fallback 与 provenance。
11. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
12. 不提交完整 solve_reports。
```

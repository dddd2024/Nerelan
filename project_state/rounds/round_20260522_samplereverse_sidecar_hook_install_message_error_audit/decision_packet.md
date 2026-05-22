```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_sidecar_hook_install_message_error_audit_20260522",
  "round_id": "round_20260522_samplereverse_sidecar_hook_install_message_error_audit",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 Codex 报告 `report_samplereverse_sidecar_hook_install_vs_compareprobe_divergence_20260521` 是可信的 `PARTIAL / REWORK_REQUIRED`：它没有把失败伪装成成功，并补充了 hook-install 层面的可观察字段。但核心目标仍未完成：sidecar 已到达 `script_load_status=loaded`、`spawn_attach_resume_status=resumed`、`ui_trigger_status=button_triggered`，却仍然没有确认 `hooks_installed`，`hook_count=0`、`requested_hook_count=3`。同时，当前代码里 `frida_message_error_count = len(script_errors)` 存在语义风险：它统计的是 Python/脚本异常列表，不是 Frida message error 列表，可能掩盖 `compare_pre_compare_handoff_target_error`。

本轮目标不是推进候选搜索，也不是运行 Base64/RC4 breakpoint probe，而是修复并验证 sidecar hook-install observability 的可信度，尤其是 Frida message error、per-hook install result、hooks_installed stage 是否 seen。

## 1. Goal

本轮目标：

```text
1. 审计并修复 compare_pre_compare_handoff_target_probe.py 中 hook-install observability 的错误或不完整之处。
2. 明确区分 Frida message error、Python exception、script load/compile error、hook install error。
3. 对 0x258c / 0x2559 / 0x1b50 三个 bounded hook point 输出逐点 install result。
4. 解释 script.load 已返回 loaded 后，为什么没有可信的 hooks_installed/hook_count 证据。
5. 继续保持 CompareProbe fallback 只作为 diagnostic，不得把 fallback compare args 当作 provenance。
6. 保持 two-candidate bounded scope；不新增候选，不扩大 beam/budget/topN/frontier iteration，不运行 Base64/RC4 breakpoint probe。
```

最低可接受推进：

```text
A. 修复 frida_message_error_count 的语义，使其真实统计 Frida message error 数量。
B. artifact 能明确输出 hooks_installed_stage_seen、hook_install_error_count、python_exception_count、per_hook_install_results。
C. 如果仍无法确认 hook install，必须明确说明是 JS 没执行到 send、message handler 未收到、Interceptor.attach 失败、module/offset 问题、进程提前结束、还是环境 BLOCKED。
D. 如果关键日志/artifact 不足以判断，report.status 必须是 BLOCKED 或 PARTIAL，不得写 SUCCESS。
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

上一轮 Codex runtime artifact 摘要：

```text
run_name = sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1
classification = instrumentation_incomplete
instrumentation_failure_stage = timeout_before_hook_install
root_cause_hypothesis = timeout_before_hook_install
hook_install_status = not_confirmed
hook_count = 0
requested_hook_count = 3
script_load_status = loaded
script_load_error = empty
frida_message_error_count = 0
spawn_attach_resume_status = resumed
ui_trigger_status = button_triggered
helper_observation_count = 0
static_compare_observation_count = 0
same_process_compare_args_captured = false
diagnostic_compare_args_captured = true
compare_probe_fallback_used = true
compare_probe_fallback_is_provenance = false
runtime_backed_writer_identified = false
project_progress_log_handling = untouched
```

上一轮审计结论：

```text
REWORK_REQUIRED

原因：
1. decision/report 绑定正确，但核心目标仍未完成。
2. Codex 只把 no-hook 现象细化到 loaded/resumed/button_triggered/hook_count=0/requested=3，没有解释 3 个 hook 为什么都未确认安装。
3. compare_pre_compare_handoff_target_probe.py 中 frida_message_error_count = len(script_errors) 语义可疑，可能没有统计 Frida message error。
4. 本轮 sidecar artifact 未提交到 GitHub，网页侧只能复核 report/pytest_result，不能直接复核 runtime JSON。
5. round_manifest.source_git_commit 仍可能偏旧，archive provenance 需要谨慎对待。
```

artifact freshness 现状：

```text
current in live artifact_index.latest_artifacts_v2:
  compare_probe
  compare_probe_log
  compare_real_lhs_provenance_audit
  run_manifest
  summary

本轮 sidecar artifact 不在 live artifact_index.latest_artifacts_v2 current 范围内。
不得把本轮 sidecar artifact 当作 live indexed current artifact，除非重新 build project_state 并明确 source_run/freshness。
```

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
project_state/rounds/round_20260521_samplereverse_sidecar_hook_install_vs_compareprobe_divergence/round_manifest.json
project_state/rounds/round_20260521_samplereverse_sidecar_hook_install_vs_compareprobe_divergence/git_diff.patch
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

允许有界读取上一轮 sidecar artifacts/logs，但不得扫描完整 `solve_reports/`：

```text
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.log
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_hook_install_vs_compareprobe_divergence_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.log
```

如果上述 artifact/log 本地不存在，不要扫描完整 `solve_reports/`；报告 `BLOCKED`，或者重新运行 bounded sidecar 并说明缺失路径。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 为什么上一轮是 REWORK_REQUIRED，而不是 ACCEPTED。
3. on_message 中 compare_pre_compare_handoff_target_error 如何进入 messages。
4. errors 与 script_errors 的语义差异。
5. frida_message_error_count 当前是否错误统计为 len(script_errors)。
6. hook_install_error_count 应如何统计。
7. hooks_installed stage 是否可能 hook_count=0 但仍应出现。
8. 如果 hooks_installed stage 完全没有出现，原因更可能是 JS 未执行到 send、message handler 未接收、进程被杀、script source 语法/运行异常，还是 hook loop 被提前中断。
9. 每个 hook point 的 install result 是否可逐点输出：0x258c, 0x2559, 0x1b50。
10. CompareProbe fallback 为什么能捕获 diagnostic compare args；它和 sidecar 的 Frida script lifecycle / hook schema / wait condition / process lifetime 有哪些仍未解释的差异。
11. 是否需要重建 project_state；如需要只能运行 project_state build/status，不得手动编辑 state JSON。
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

必须修复或明确证明无需修复：

```text
1. frida_message_error_count 应统计 Frida message error 数量，而不是只统计 script_errors。
2. artifact 必须区分：
   - python_exception_count
   - frida_message_error_count
   - hook_install_error_count
   - hooks_installed_stage_seen
   - hooks_installed_stage_hook_count
   - per_hook_install_results
3. per_hook_install_results 至少包含每个 hook point 的 name、module_offset、install_status、address、error。
4. 如果 hooks_installed stage seen 但 hook_count=0，应输出 hook loop completed with zero installed，而不是 generic timeout。
5. 如果 hooks_installed stage not seen，但 script_load_status=loaded，应输出具体 root_cause_evidence，说明 stage message 缺失点。
```

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
A. 修复 hook install observability，artifact 能确认 hooks_installed_stage_seen/hook_count/per_hook_install_results。
B. 明确定位 hook install 失败原因，例如 module/offset invalid、Interceptor.attach failed、message handler missed stage、JS execution interrupted。
C. 如果仍不能定位，报告 BLOCKED，并说明缺失的最小日志或环境条件。
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
hooks_installed_stage_seen
hooks_installed_stage_hook_count
per_hook_install_results
hook_install_error_count
python_exception_count
frida_message_error_count
script_load_status
script_load_error
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

必须新增或更新测试覆盖：

```text
1. Frida message error 与 Python exception 分开统计。
2. compare_pre_compare_handoff_target_error 会增加 frida_message_error_count 或 hook_install_error_count。
3. script load/compile exception 会增加 python_exception_count 或 script_load_error，不应伪装为 hook install error。
4. hooks_installed stage seen 但 hook_count=0 时，classification/root_cause_evidence 不能只是 generic timeout。
5. hooks_installed stage not seen 且 script_load_status=loaded 时，artifact 要明确 stage message 缺失。
6. per_hook_install_results 必须包含 0x258c / 0x2559 / 0x1b50 三个 bounded hook point。
7. CompareProbe fallback 不能使 runtime_backed_last_writer_identified 成立。
8. candidate set remains exactly two bounded candidates unless explicit fixture overrides it。
```

如果 runtime 环境可用，必须重新跑 bounded sidecar，并记录：

```text
run_name
candidate_inputs_hex
hooks_installed_stage_seen
hooks_installed_stage_hook_count
hook_install_status
hook_count
requested_hook_count
per_hook_install_results
hook_install_error_count
frida_message_error_count
python_exception_count
script_load_status
script_load_error
spawn_attach_resume_status
ui_trigger_status
helper_observation_count
static_compare_observation_count
same_process_compare_args_captured
diagnostic_compare_args_captured
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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260522_samplereverse_sidecar_hook_install_message_error_audit
```

注意：

```text
如果仍无法确认 hook install，report.status 必须是 PARTIAL 或 BLOCKED，不得是 SUCCESS。
如果关键 artifact/log 缺失导致无法判断，report.status 必须是 BLOCKED。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 仍只能得到 loaded/resumed/button_triggered/hook_count=0，但不能说明 hooks_installed stage 是否 seen。
2. 无法区分 Frida message error 与 Python exception。
3. 无法输出 per-hook install result。
4. 无法读取必要 sidecar/CompareProbe logs，也无法重新运行 bounded sidecar。
5. 需要回旧 sample_solver。
6. 需要只靠扩大 beam/budget/topN/timeout 才能推进。
7. 需要在 real LHS writer/provenance 识别前运行 Base64/RC4 breakpoint probe。
8. 需要把 stale artifact 当作 current evidence。
9. 需要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
10. 需要读取或提交完整 solve_reports。
11. 需要使用 compare_semantics_agree=false candidate 作为主线。
12. 需要把 CompareProbe fallback 当成 provenance。
13. 无法保证 compare args 与 write events 来自同一 process/thread，却仍想输出 runtime_backed_last_writer_identified。
14. 无法让 report.based_on_decision_id 绑定当前 decision_id。
15. 无法让 pytest_result.txt 记录真实测试和 runtime/blocked 状态。
16. 需要继续写 PROJECT_PROGRESS_LOG.txt。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary 存在，based_on_decision_id 指向 decision_samplereverse_sidecar_hook_install_message_error_audit_20260522。
2. report.status 不得在 hook install 未确认时写 SUCCESS。
3. frida_message_error_count / python_exception_count / hook_install_error_count 语义正确且有测试覆盖。
4. hooks_installed_stage_seen 明确记录。
5. per_hook_install_results 包含 0x258c / 0x2559 / 0x1b50。
6. 如果 sidecar 仍失败，root_cause_evidence 必须比 timeout_before_hook_install 更具体。
7. CompareProbe fallback 仍为 diagnostic-only，compare_probe_fallback_is_provenance=false。
8. 不破坏 PROJECT_PROGRESS_LOG.txt revert，且不再修改 PROJECT_PROGRESS_LOG.txt。
9. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
10. 没有运行 Base64/RC4 breakpoint probe。
11. 没有回旧 solver 或扩大搜索。
12. 保持两个 bounded candidates，不新增候选搜索。
13. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
14. 不提交完整 solve_reports。
```

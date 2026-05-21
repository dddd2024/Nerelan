```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_sidecar_no_hook_observation_root_cause_20260521",
  "round_id": "round_20260521_samplereverse_sidecar_no_hook_observation_root_cause",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 `decision_samplereverse_sidecar_compare_args_scope_fix_20260521` 的 Codex 报告自评为 `SUCCESS / ACCEPTED`，但 GPT 审计结论为 `REWORK_REQUIRED`。原因不是 handoff 绑定失败，而是 runtime 证据链退化：上一轮之前的 sidecar 至少达到 `followed_thread_count=1` / `raw_write_count=323`，而最新 sidecar 退回 `followed_thread_count=0` / `raw_write_count=0` / `timeout_waiting_for_hook_observation`。这不满足当前计划里“如果仍无法捕获 same-process compare args，必须给出更具体、可执行 instrumentation_failure_stage，不得只写 generic timeout”的最低要求。

本轮目标不是推进新搜索，也不是扩大运行参数，而是返工解释 no-hook-observation 的根因，并修正报告状态可信度。

## 1. Goal

本轮只做返工，不推进新候选搜索。

目标：

```text
1. 承认上一轮 report 不应标记 SUCCESS；如果本轮仍只有 generic timeout，report.status 必须是 PARTIAL 或 BLOCKED，不得写 SUCCESS。
2. 审计为什么 sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1 退回 no hook observation。
3. 对比 sr_lhs_last_writer_sidecar_fix_20260521_r1 为什么能 followed_thread_count=1 / raw_write_count=323。
4. 找出新 wait-loop / stop-condition 修改是否导致 helper observation、thread follow、write monitor health 被丢失。
5. 不允许只输出 timeout_waiting_for_hook_observation；必须定位更具体原因，或者明确 BLOCKED 并说明缺什么日志/环境。
6. 保持 two-candidate bounded sidecar，不新增候选、不扩大搜索、不运行 Base64/RC4 breakpoint probe。
```

最低可接受推进：

```text
A. 如果找到根因：artifact/report 必须写出具体 failure stage，例如 hook_install_failed、module_offset_mismatch、spawn_attach_resume_failed、ui_trigger_failed、helper_hook_not_reached、script_output_missing、log_path_missing、timeout_before_hook_install、timeout_after_ui_trigger_before_helper、compare_probe_sidecar_invocation_divergence。
B. 如果找不到根因：report 必须是 PARTIAL 或 BLOCKED，并明确列出缺失的 bounded artifact/log，不得标 SUCCESS。
C. 不破坏上一轮已完成的 PROJECT_PROGRESS_LOG.txt revert。
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

当前 live state 仍来自 sample state：

```text
round_id = round_20260520_052928
state_build_id = state_20260520_052928_8a77e6637c6c
state_digest = 8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d
source_harness_run = sr_lhs_thread_follow_timing_20260520_r4
active_strategy = CompareAwareSearchStrategy
current_bottleneck.reason = compare_lhs_runtime_backed_writer_missing
current_bottleneck.stage = compare_real_lhs_provenance_audit
```

当前 best candidates 固定为：

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
REWORK_REQUIRED

原因：
1. report 自评 SUCCESS/ACCEPTED 过高。
2. PROJECT_PROGRESS_LOG.txt 问题已修，但这只是 handoff 清理，不是核心 runtime 推进。
3. sidecar runtime 从 followed_thread_count=1/raw_write_count=323 退回到 0/0。
4. instrumentation_failure_stage 仍是 generic timeout，不满足本轮“不得只写 generic timeout”的要求。
5. 没有解释为什么 CompareProbe fallback 能捕获 compare args，而 bounded sidecar 完全没有 hook observation。
```

上一轮成功完成的 handoff 修复：

```text
PROJECT_PROGRESS_LOG.txt 中上一轮越界写入块已被 revert。
files_changed 已如实列出 PROJECT_PROGRESS_LOG.txt。
不要再次写入 PROJECT_PROGRESS_LOG.txt。
```

需要对比的两个 runtime 结果：

```text
Previous better diagnostic run:
  run_name = sr_lhs_last_writer_sidecar_fix_20260521_r1
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

Latest regressed run:
  run_name = sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1
  classification = instrumentation_incomplete
  instrumentation_failure_stage = timeout_waiting_for_hook_observation
  same_process_compare_args_captured = false
  diagnostic_compare_args_captured = true
  compare_probe_fallback_used = true
  compare_probe_fallback_is_provenance = false
  write_monitor_health.observed_candidate_count = 2
  write_monitor_health.followed_thread_count = 0
  write_monitor_health.raw_write_count = 0
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

stale / legacy:
  base64_rc4_static_point_discovery
  compare_handoff_return_site_probe
  compare_producer_material_confirmation
  function_semantic_audit
  frontier_summary
  guided_pool_result
  guided_pool_validation
  pairscan_summary
  smt_result
  strata_summary

not in live artifact_index.latest_artifacts_v2:
  sr_lhs_last_writer_sidecar_fix_20260521_r1 compare_lhs_last_writer_provenance_audit
  sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1 compare_lhs_last_writer_provenance_audit
```

这些 sidecar artifacts 可从本地路径有界读取，但不得当作 live indexed current artifact。

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
project_state/rounds/round_20260521_samplereverse_sidecar_compare_args_scope_fix/round_manifest.json
project_state/rounds/round_20260521_samplereverse_sidecar_compare_args_scope_fix/git_diff.patch
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
```

允许有界读取 current artifacts：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.log
```

允许有界读取两个 sidecar run：

```text
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*

solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*
```

如果上述 artifact/log 本地不存在，不要扫描完整 `solve_reports/`；report 标记 `BLOCKED` 或重新运行 bounded sidecar，并说明缺失路径。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 为什么上一轮 GPT 审计给 REWORK_REQUIRED。
3. 为什么上一轮 report 的 SUCCESS/ACCEPTED 不可信。
4. `PROJECT_PROGRESS_LOG.txt` revert 是否仍保持，不得再次修改该文件。
5. 对比两个 run 的 candidate logs：
   - sr_lhs_last_writer_sidecar_fix_20260521_r1
   - sr_lhs_last_writer_sidecar_compare_args_scope_fix_20260521_r1
6. 旧 run 为什么能 followed_thread_count=1/raw_write_count=323。
7. 新 run 为什么 no hook observation / followed_thread_count=0/raw_write_count=0。
8. Frida hook 是否安装成功，hook_count 是多少。
9. target 是否 spawn / attach / resume 成功。
10. UI window 是否连接成功，input 是否注入成功，button 是否触发成功。
11. helper hook `0x1b50` 是否被命中；如果没有，原因是 hook 未安装、RVA 错、目标路径未到、UI 未触发，还是 log 缺失。
12. static compare hook `0x258c` 是否被命中；如果命中但无 args，要标 argument_extraction_failed；如果没命中，要说明停在哪个 stage。
13. CompareProbe fallback 为什么仍能捕获 diagnostic compare args：对比两者 hook 地址、module base/RVA conversion、输入触发、stop condition、process lifetime。
14. 是否需要重建 project_state；如需要只能运行 project_state build/status，不得手动编辑 state JSON。
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

修改目的只能是复用 compare arg capture 逻辑、增加 bounded stage logging、或统一 hook schema，不得改变 CompareProbe 既有语义。

允许生成 runtime artifact，但不要提交完整 solve_reports：

```text
solve_reports/harness_runs/<run_name>/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
```

允许归档：

```text
project_state/rounds/round_20260521_samplereverse_sidecar_no_hook_observation_root_cause/*
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
A. 恢复到至少 helper/write monitor 可观察状态，并解释为何还不到 0x258c。
B. 捕获 same-process 0x258c compare args，并进入 compare_reached_but_writer_missing 或 runtime_backed_last_writer_identified。
C. 若仍 no hook observation，必须输出具体 stage-root-cause，不得只写 timeout_waiting_for_hook_observation。
D. 若 artifact/log 缺失或 runtime 环境不可用，classification = blocked_by_environment 或 report.status = BLOCKED。
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
last_writer 或 last_writer_candidates
bounded_failures
instrumentation_failure_stage
root_cause_hypothesis
root_cause_evidence
hook_install_status
hook_count
spawn_attach_resume_status
ui_trigger_status
helper_observation_count
static_compare_observation_count
candidate_log_paths
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
next_allowed_probe 必须仍然是 bounded last-writer / instrumentation 修复方向，不得跳到 Base64/RC4 probe。
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
spawn_attach_resume_status
ui_trigger_status
helper_observation_count
static_compare_observation_count
same_process_compare_args_captured
followed_thread_count
raw_write_count
compare_probe_fallback_used
compare_probe_fallback_is_provenance=false
root_cause_hypothesis
root_cause_evidence
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260521_samplereverse_sidecar_no_hook_observation_root_cause
```

注意：

```text
如果最终仍只有 generic timeout，report.status 必须是 PARTIAL，不得是 SUCCESS。
如果关键 artifact/log 缺失导致无法判断，report.status 必须是 BLOCKED。
```

### 7.1 Required unit tests

新增或更新测试必须覆盖：

```text
1. generic timeout without root_cause_hypothesis must not map to SUCCESS-style artifact claim。
2. no hook observation must include hook_install_status / spawn_attach_resume_status / ui_trigger_status fields。
3. helper observed but static compare missing maps to stop_condition_before_compare。
4. static compare observed without args maps to argument_extraction_failed。
5. fallback fields cannot make runtime_backed_last_writer_identified。
6. same-process compare args + raw writes but no intersecting write maps to compare_reached_but_writer_missing。
7. candidate set remains exactly two bounded candidates unless an explicit test fixture overrides it。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 只能得到 generic timeout，且不能给出 root cause evidence。
2. 无法读取两个 sidecar run 的 candidate logs，也无法重新运行 bounded sidecar。
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
1. codex_report_summary 存在，based_on_decision_id 指向 decision_samplereverse_sidecar_no_hook_observation_root_cause_20260521。
2. 如果结果仍是 no hook observation / generic timeout，report.status 不能是 SUCCESS。
3. 必须解释 latest run 从 followed_thread_count=1/raw_write_count=323 退化到 0/0 的原因，或明确 BLOCKED。
4. 必须对比 CompareProbe fallback 与 sidecar 的可观察性差异。
5. 不破坏 PROJECT_PROGRESS_LOG.txt revert，且不再修改 PROJECT_PROGRESS_LOG.txt。
6. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
7. 没有运行 Base64/RC4 breakpoint probe。
8. 没有回旧 solver 或扩大搜索。
9. 保持两个 bounded candidates，不新增候选搜索。
10. artifact 明确区分 diagnostic fallback 与 provenance。
11. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
12. 不提交完整 solve_reports。
```

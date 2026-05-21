```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_fix_lhs_last_writer_sidecar_no_observations_20260521",
  "round_id": "round_20260521_samplereverse_fix_lhs_last_writer_sidecar_no_observations",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 `decision_samplereverse_compare_lhs_last_writer_provenance_20260521` 的 Codex 报告为 `PARTIAL`：新增了 `compare_lhs_last_writer_provenance_audit` 入口并生成了 artifact 摘要，但 runtime sidecar 实际没有 scripted hook observations，两个 bounded candidates 均出现 timeout / no observations；CompareProbe fallback 可以捕获 `0x258c` arg0/preview，但 fallback 明确不是 last-writer provenance。

本轮目标不是继续候选搜索，也不是运行 Base64/RC4 breakpoint probe，而是修复或重构 last-writer sidecar 的观测链路，使同一次 debugger/process/thread 内能够同时采集 compare args 与 write monitor evidence，或者输出比上一轮更具体、可执行的 instrumentation failure reason。

## 1. Goal

本轮目标：

```text
1. 审计上一轮新增的 compare_lhs_last_writer_provenance.py 为什么只是 wrapper 且运行后 scripted_hook_no_observations / returncode=124。
2. 审计 compare_pre_compare_handoff_target_probe.py 的参数、hook point 解析、thread-follow activation、timeout / stop condition、output schema，确认为什么未观测到 0x258c / 0x2559 / 0x1b50。
3. 修复 last-writer sidecar，使它不依赖跨进程 CompareProbe fallback 来假装 provenance。
4. 如果使用 fallback，只能作为 compare arg diagnostic，不得把 fallback 捕获的 arg0 地址与另一进程的 write_ring 强行关联。
5. 重新运行 bounded two-candidate sidecar，产出新的 compare_lhs_last_writer_provenance_audit.json。
6. 如果确认 writer，必须是 runtime-backed 且与同一次 compare arg0 buffer 连接。
7. 如果仍未确认 writer，classification 必须是 instrumentation_incomplete 或 compare_reached_but_writer_missing，并写清具体失败阶段。
```

最低可接受推进不是必须找到 writer，而是把上一轮过粗失败原因：

```text
write monitor did not follow a runtime thread
scripted_hook_no_observations
returncode=124
```

细化成可执行的原因，例如：

```text
hook points file schema mismatch
script does not support 0x258c hook kind
module base / RVA conversion mismatch
target process reached compare but script stopped before hook install
thread selection / follow activation bug
timeout before sample execution reaches compare
write monitor requires compare args captured in same script path
Olly automation cannot combine write trace with compare arg capture in this script
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

当前 best candidates：

```text
exact2:
  candidate_hex = 78d540b49c59077041414141414141
  runtime_ci_distance5 = 246
  runtime_ci_exact_wchars = 2
  compare_semantics_agree = true

exact1/frontier:
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

上一轮 Codex 报告的关键事实：

```text
report_id = report_samplereverse_compare_lhs_last_writer_provenance_20260521
based_on_decision_id = decision_samplereverse_compare_lhs_last_writer_provenance_20260521
status = PARTIAL
acceptance_recommendation = NEEDS_REVIEW
new artifact classification = instrumentation_incomplete
scripted_hook_status = scripted_hook_no_observations for both bounded candidates
scripted_returncode = 124 for both bounded candidates
compare_probe_fallback_status = compare_probe_fallback_captured_compare_args
compare_probe_fallback_is_provenance = false
write_monitor_health = followed_thread_count=0 raw_write_count=0 ring_capacity=4096
runtime_backed_writer_identified = false
```

artifact freshness 现状：

```text
current:
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

missing in live artifact_index.latest_artifacts_v2:
  base64_rc4_breakpoint_probe
  compare_lhs_producer_audit
  compare_lhs_slot_writer_predecessor_audit
  compare_lhs_slot_writer_source_audit
  compare_lhs_upstream_writer_audit
  compare_producer_trace_probe
  dynamic_compare_path_probe
  material_hook_runtime_validation
  post_handoff_exception_unwind_audit
  pre_rc4_material_probe
```

上一轮新 artifact：

```text
solve_reports/harness_runs/sr_lhs_last_writer_provenance_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
```

只在 `codex_execution_report.md` 和归档摘要中出现；它没有进入 live `artifact_index.latest_artifacts_v2`。本轮可在本地有界读取该 run 的 artifact 和 candidate logs 来解释 instrumentation failure；若本地 artifact 缺失，应重新运行 bounded sidecar 生成，不要扫描完整 `solve_reports/`。

## 3. Do Not Do

不要做以下事情：

```text
不要继续 harness Phase 3 hardening。
不要修改 docs/phase2_harness_reproducibility_completion.md。
不要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
不要把上一轮 compare_probe_fallback 捕获的 arg0 地址当作 last-writer provenance。
不要跨进程、跨 run、跨 candidate 强行合并 compare arg0 地址和 write_ring 事件。
不要回旧 sample_solver 盲搜。
不要扩大 beam、topN、budget、timeout、frontier iteration 作为推进方式。
不要使用 compare_semantics_agree=false candidates 作为 primary frontier。
不要重复 exact2 basin value-pool evaluation。
不要重复 H1/H3 fixed boundary contrast set。
不要重复当前 5-candidate transform trace consistency audit，除非新增 runtime evidence。
不要在识别 runtime-backed real LHS producer / writer 前运行 Base64/RC4 breakpoint probe。
不要复用旧 [ebp-0x1170] 作为真实 LHS 来源，除非本轮拿到 runtime-backed provenance。
不要重复 producer material confirmation，除非新增 instruction-level evidence。
不要把 0x4019e0 / 0x401b50 / 0x4018cd / 0x401be3 当成 Base64/RC4 material producer，除非新增语义证据。
不要提交完整 solve_reports。
不要默认读取完整 solve_reports。
不要默认读取完整 PROJECT_PROGRESS_LOG.txt。
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
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/compare_probe.py
tests/test_compare_aware_search_strategy.py
```

必须有界读取 current artifacts：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.log
```

允许有界读取上一轮新 artifact 和 candidate logs，仅用于解释 instrumentation failure：

```text
solve_reports/harness_runs/sr_lhs_last_writer_provenance_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_provenance_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_1/*
solve_reports/harness_runs/sr_lhs_last_writer_provenance_20260521_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/candidate_2/*
```

如果上一轮 artifact 不存在，不要扫描完整 `solve_reports/`；直接重新运行 bounded sidecar 并在 report 中说明 artifact missing。

允许有界参考 stale artifacts，但不得当 current 证据：

```text
solve_reports/tool_artifacts/samplereverse_base64_rc4_static_point_discovery_20260508/base64_rc4_static_point_discovery.json
solve_reports/tool_artifacts/samplereverse_handoff_return_outcome_manual_20260510/function_semantic_audit/function_semantic_audit.json
```

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 上一轮 report status 为什么是 PARTIAL，而不是 SUCCESS。
3. 上一轮 compare_lhs_last_writer_provenance_audit 的 classification、scripted_hook_status、returncode、write_monitor_health、fallback status。
4. compare_lhs_last_writer_provenance.py 目前是否只是 wrapper；如果是，wrapper 传入的 points/args 是否被底层脚本正确解释。
5. compare_pre_compare_handoff_target_probe.py 是否支持 0x258c / 0x2559 / 0x1b50 的 hook point schema。
6. timeout=124 发生在 hook install 前、目标执行前、等待 compare 前，还是 cleanup/exit 阶段。
7. thread-follow activation 为什么 followed_thread_count=0。
8. CompareProbe 为什么能捕获 0x258c，而 last-writer sidecar 不能；二者在启动方式、hook 地址、模块基址解析、输入注入、stop condition 上有什么差异。
9. 是否存在跨进程 fallback / write_ring 合并风险；若存在，必须消除或在 artifact 中显式标记 fallback_not_provenance。
10. 是否需要将 compare arg capture 和 write monitor 放入同一脚本路径、同一 process、同一 thread。
11. 本轮是否需要重建 project_state；若需要，只能运行 project_state build/status，不要手动编辑 state JSON。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有确认为必要时，才允许小幅修改：

```text
reverse_agent/olly_scripts/compare_probe.py
```

修改目的只能是复用 compare arg capture 逻辑或统一 hook schema，不得改变 CompareProbe 既有语义。

允许生成 runtime artifact，但不要提交完整 solve_reports：

```text
solve_reports/harness_runs/<run_name>/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
```

允许归档：

```text
project_state/rounds/round_20260521_samplereverse_fix_lhs_last_writer_sidecar_no_observations/*
```

不要修改：

```text
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

修复后的 sidecar 必须保持 bounded：

```text
compare site: 0x258c
post_handoff_lhs_reload: 0x2559
bounded helper candidate: 0x1b50
candidate 1: 78d540b49c59077041414141414141
candidate 2: 5a3e7f46ddd474d041414141414141
```

必须做到以下之一：

```text
A. 同一次 script/process/thread 内捕获 compare args + write monitor events，且 runtime-backed writer 连接到 arg0 buffer。
B. 同一次 script/process/thread 内捕获 compare args，但 write monitor 没有 intersecting write；classification = compare_reached_but_writer_missing，并记录 followed_thread_count/raw_write_count/filter count。
C. 仍无法捕获 compare args 或无法 follow thread；classification = instrumentation_incomplete，并记录具体失败阶段，不得只写 generic timeout。
D. 环境或 Olly automation 阻塞；classification = blocked_by_environment，并记录环境缺口。
```

如果使用 CompareProbe fallback：

```text
1. fallback 只能填充 diagnostic fields。
2. artifact 必须包含 compare_probe_fallback_is_provenance = false。
3. 不能把 fallback arg0 地址与另一进程/另一 run 的 write events 关联成 runtime-backed writer。
4. 若需要 provenance，必须在同一 sidecar run 内捕获 compare args 与 write events。
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
arg0_lhs_ptr
arg0_lhs_preview
same_process_provenance: true/false
compare_probe_fallback_used: true/false
compare_probe_fallback_is_provenance: false when used
write_monitor_health
last_writer 或 last_writer_candidates
bounded_failures
instrumentation_failure_stage
next_allowed_probe
base64_rc4_breakpoint_probe_run = false
candidate_generation_changed = false
beam_budget_topn_timeout_frontier_limit_expanded = false
```

如果确认 writer：

```text
last_writer.instruction
last_writer.address
last_writer.module_offset
last_writer.write_size
last_writer.write_preview
last_writer.candidate_hex
last_writer.same_process = true
last_writer.same_thread_or_thread_id = ...
last_writer.connects_to_actual_arg0 = true
```

如果没有确认 writer：

```text
bounded_failures 必须可执行，不得只写 unknown 或 timeout。
next_allowed_probe 必须仍然是 bounded last-writer / instrumentation 修复方向，不得跳到 Base64/RC4 probe。
```

## 7. Tests

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_lhs_last_writer_provenance.py reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py reverse_agent\strategies\compare_aware_search.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "compare_lhs_last_writer or compare_real_lhs_last_writer or pre_compare_handoff"
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
```

如果修改 `compare_probe.py`，额外运行：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_probe.py
```

如果 runtime 环境可用，必须运行 bounded sidecar 并记录：

```text
run_name
candidate_inputs_hex
artifact path
classification
是否到达 0x258c
是否在同一 process/thread 捕获 compare args 与 write monitor
scripted_hook_status
scripted_returncode
write_monitor_health
runtime_backed_writer_identified
compare_probe_fallback_used
compare_probe_fallback_is_provenance
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260521_samplereverse_fix_lhs_last_writer_sidecar_no_observations
```

注意：

```text
本轮 report 写入前，lint-report 可能显示旧 report consumed by non-success report 或 based_on_decision_id mismatch。
这属于 pre-report expected state，必须记录。
最终 report 写入后，lint-report / lint-handoff 必须恢复为 OK 或给出明确 PARTIAL/BLOCKED 原因。
```

### 7.1 Required unit tests

新增或更新测试必须覆盖：

```text
1. fallback fields cannot make runtime_backed_last_writer_identified when same_process_provenance=false。
2. scripted_hook_no_observations + returncode=124 must classify instrumentation_incomplete with instrumentation_failure_stage。
3. followed_thread_count=0 must produce bounded failure "thread follow not activated" or equivalent precise reason。
4. same-process compare args + intersecting write events can classify runtime_backed_last_writer_identified。
5. same-process compare args + raw writes but no intersecting write can classify compare_reached_but_writer_missing。
6. candidate set remains exactly two bounded candidates unless an explicit test fixture overrides it。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 需要回旧 sample_solver。
2. 需要只靠扩大 beam/budget/topN/timeout 才能推进。
3. 需要在 real LHS writer/provenance 识别前运行 Base64/RC4 breakpoint probe。
4. 需要把 stale artifact 当作 current evidence。
5. 需要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
6. 需要读取或提交完整 solve_reports。
7. 需要使用 compare_semantics_agree=false candidate 作为主线。
8. 需要重复 negative_results 中已禁止的 exact2 basin 或 H1/H3 contrast 方向。
9. 需要把 CompareProbe fallback 当成 provenance。
10. 无法保证 compare args 与 write events 来自同一 process/thread，却仍想输出 runtime_backed_last_writer_identified。
11. 无法让 report.based_on_decision_id 绑定当前 decision_id。
12. 无法让 pytest_result.txt 记录真实测试和 runtime/blocked 状态。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary 存在，based_on_decision_id 指向 decision_samplereverse_fix_lhs_last_writer_sidecar_no_observations_20260521。
2. 没有继续 harness Phase 3 工作。
3. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
4. 没有运行 Base64/RC4 breakpoint probe。
5. 没有回旧 solver 或扩大搜索。
6. 明确解释上一轮 scripted_hook_no_observations / returncode=124 / followed_thread_count=0 的原因。
7. 修复或重构 bounded last-writer sidecar，使 compare args 与 write monitor 尽量在同一 process/thread 捕获。
8. 重新生成 compare_lhs_last_writer_provenance_audit.json，classification 清楚。
9. artifact 明确区分 diagnostic fallback 与 provenance。
10. 如果确认 writer，必须是 same-process runtime-backed。
11. 如果仍没有确认 writer，必须给出具体、可执行的 instrumentation_failure_stage 和 bounded_failures。
12. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
13. 不提交完整 solve_reports。
```

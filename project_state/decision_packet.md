```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260523_samplereverse_sidecar_hooks_installed_observation_blocker",
  "round_id": "round_20260523_samplereverse_sidecar_hooks_installed_observation_blocker",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 `report_samplereverse_sidecar_subprocess_lifecycle_blocker_20260522` 是可信的 `BLOCKED / REWORK_REQUIRED`：它已经把阻断点从早期 `not_started / initial_payload_only` 推进并收窄到 `script_load_status=loaded`、`spawn_attach_resume_status=resumed`、`ui_trigger_status=button_triggered`、`scripted_lifecycle_entered=true`、`scripted_last_runtime_stage=waiting_for_observation`，但仍没有观察到 `hooks_installed` 阶段和任何 same-process hook observation。因此本轮目标不是重新诊断 subprocess 是否启动，而是解释 loaded Frida script 为什么没有上报 hook 安装状态，或者修复 hook install acknowledgement / message bridge，使 sidecar 能明确区分 hook 脚本未执行、hook 安装异常、message handler 丢事件、hook 点未命中四类状态。

## 1. Goal

本轮目标：

```text
1. 继续固定 two-candidate bounded sidecar，不新增候选，不扩大搜索。
2. 审计 compare_lhs_last_writer_provenance sidecar 中 Frida script create/load/resume/message callback/acknowledgement 的完整路径。
3. 定位为什么 child 已到 waiting_for_observation，却没有记录 hooks_installed stage。
4. 明确区分：
   - script loaded but JS top-level did not execute
   - JS executed but hooks_installed message lost
   - hook install threw exception before acknowledgement
   - hooks installed but hook points never hit
   - process/module base/address resolution wrong
   - message callback/JSON serialization/filtering bug
5. 修复或增加最小观测字段，使 artifact 能记录 hook-install acknowledgement、per-hook install result、script message sequence、last JS stage、message handler health。
6. 如果 hook 点地址或 module base 解析错误，给出 bounded correction；不要扩大到 Base64/RC4 probe 或候选搜索。
7. 如果环境或 Frida 行为导致无法继续，报告 BLOCKED，并给出缺失的最小环境条件和日志。
```

最低可接受推进：

```text
A. 当前 root cause 必须比 hooks_installed_stage_missing_after_script_load 更具体。
B. artifact 必须能说明：JS top-level 是否执行、hooks_installed message 是否发送、Python callback 是否收到、per-hook install 是否成功。
C. 如果仍无 same-process observations，必须能判断是 hook installation failure 还是 hook not hit。
D. CompareProbe fallback 仍只能是 diagnostic-only，不能作为 runtime-backed writer provenance。
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

上一轮 `codex_execution_report.md` 的关键事实：

```text
report_id = report_samplereverse_sidecar_subprocess_lifecycle_blocker_20260522
based_on_decision_id = decision_samplereverse_sidecar_subprocess_lifecycle_blocker_20260522
status = BLOCKED
acceptance_recommendation = REWORK_REQUIRED
classification = instrumentation_incomplete
instrumentation_failure_stage = hooks_installed_stage_missing_after_script_load
root_cause_hypothesis = hooks_installed_stage_missing_after_script_load
subprocess_returncode = 124
subprocess_timed_out = true
scripted_output_exists = true
scripted_output_size_bytes = 3126
scripted_initial_payload_only = false
scripted_lifecycle_entered = true
scripted_last_runtime_stage = waiting_for_observation
script_load_status = loaded
script_load_error = empty
spawn_attach_resume_status = resumed
ui_trigger_status = button_triggered
hook_install_status = not_confirmed_stage_missing
hook_count = 0
requested_hook_count = 3
hooks_installed_stage_seen = false
same_process_compare_args_captured = false
diagnostic_compare_args_captured = true
compare_probe_fallback_used = true
compare_probe_fallback_is_provenance = false
runtime_backed_writer_identified = false
project_progress_log_handling = untouched
```

上一轮测试与状态记录：

```text
py_compile passed
focused pytest: 26 passed, 164 deselected
full tests/test_compare_aware_search_strategy.py: 190 passed
tests/test_project_state.py: 104 passed
project_state status/lint-decision/lint-report/lint-handoff passed with BLOCKED warnings
archive-round wrote round_manifest.source_git_commit = 6281cd719c32
```

artifact freshness 现状：

```text
current in live artifact_index.latest_artifacts_v2:
  compare_probe
  compare_probe_log
  compare_real_lhs_provenance_audit
  run_manifest
  summary

missing in live artifact_index.latest_artifacts_v2:
  compare_pre_compare_handoff_target_probe

stale in live artifact_index.latest_artifacts_v2:
  base64_rc4_static_point_discovery
  bridge_search_result
  bridge_validation
  checkpoint
  compare_aware_result
  compare_handoff_return_site_probe
  compare_producer_material_confirmation
  function_semantic_audit
  guided_pool_result
  guided_pool_validation
  pairscan_summary
  smt_result
  strata_summary

上一轮 sidecar artifact 来自 sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1，但 live artifact_index 还没有把它标为 current。Codex 可以有界读取该 artifact/log 作为上一轮报告证据，但不得把它伪装成 live indexed current artifact。
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
不要重复上一轮 subprocess startup / initial_payload_only 诊断。
不要靠扩大 timeout 当作主要推进方式。
不要把 loaded script 但无 hooks_installed 的情况标成 SUCCESS。
不要将 hook 点未命中与 hook 安装失败混为一个 timeout。
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
project_state/rounds/round_20260522_samplereverse_sidecar_subprocess_lifecycle_blocker/round_manifest.json
project_state/rounds/round_20260522_samplereverse_sidecar_subprocess_lifecycle_blocker/git_diff.patch
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/olly_scripts/compare_probe.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取 current artifacts：

```text
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.json
solve_reports/harness_runs/sr_lhs_thread_follow_timing_20260520_r4/reports/tool_artifacts/samplereverse_patched/samplereverse_patched_compare_probe.log
```

允许有界读取上一轮 sidecar artifacts/logs，但不得扫描完整 `solve_reports/`：

```text
solve_reports/harness_runs/sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.json
solve_reports/harness_runs/sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.log
solve_reports/harness_runs/sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.json
solve_reports/harness_runs/sr_lhs_last_writer_subprocess_lifecycle_blocker_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.log
```

如果上述 artifact/log 本地不存在，不要扫描完整 `solve_reports/`；报告 `BLOCKED`，或者重新运行 bounded sidecar 并说明缺失路径。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 为什么上一轮是 BLOCKED，而不是 ACCEPTED。
3. 上一轮已经证明 subprocess 启动、script loaded、target resumed、UI triggered；本轮不要重复 startup 诊断。
4. compare_lhs_last_writer_provenance.py 中 Frida script source 的 top-level 代码是否在 load 后立即发送 stage/ack message。
5. script.on('message', ...) callback 是否在 script.load() 前注册，是否可能因时序丢失早期 hooks_installed message。
6. Python message handler 是否过滤、解析、覆盖、丢弃了 JS side payload。
7. JS top-level 是否包裹 try/catch；hook install exception 是否能 send 到 Python。
8. per-hook install loop 的地址计算、module base、hook address、Interceptor.attach 是否记录 result。
9. hook points 是否位于正确进程、正确 module base、正确 instruction boundary。
10. script_load_status=loaded 后为什么 last_runtime_stage 直接停在 waiting_for_observation，而不是 hooks_installed。
11. 是否存在 UI trigger 过早，导致 hooks installed 之前目标路径已经执行完毕。
12. CompareProbe fallback 与 sidecar 的脚本、attach timing、target lifecycle、input trigger、hook 点差异。
13. 本轮 artifact 是否仍是 diagnostic-only；是否有资格更新 artifact_index current，如没有不要手动编辑 state JSON。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/olly_scripts/compare_lhs_last_writer_provenance.py
reverse_agent/strategies/compare_aware_search.py
tests/test_compare_aware_search_strategy.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有发现兼容性回归或测试必要时，才允许小幅修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
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

必须新增或保证输出：

```text
js_top_level_seen
js_top_level_timestamp
js_hooks_install_begin_seen
js_hooks_installed_seen
js_hook_install_exception_count
js_hook_install_exception_messages
python_message_callback_registered_before_load
python_message_count_total
python_message_count_by_type
python_message_decode_error_count
python_message_last_payload
per_hook_install_results
per_hook_install_error_count
module_base_resolution_status
hook_address_by_name
hook_address_validation
script_load_to_hooks_installed_elapsed_ms
script_load_to_ui_trigger_elapsed_ms
ui_trigger_after_hooks_installed
waiting_for_observation_reason
hook_not_hit_vs_hook_not_installed_classification
compare_probe_fallback_is_provenance=false
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
A. 修复 message ordering/acknowledgement，使 artifact 能看到 hooks_installed 或 hook_install_error。
B. 证明 JS top-level 没执行，并说明 Frida load/agent error 的具体证据。
C. 证明 hooks installed 但目标 hook points 未命中，并给出下一步 bounded hook-point correction。
D. 证明 hook address/module base 错误，并给出 bounded correction。
E. 如果环境无法继续，明确 BLOCKED，并说明需要的最小本地环境条件或日志。
```

如果继续使用 CompareProbe fallback：

```text
1. fallback 只能填充 diagnostic fields。
2. artifact 必须包含 compare_probe_fallback_is_provenance = false。
3. 不能把 fallback arg0 地址与另一进程/另一 run 的 write events 关联成 runtime-backed writer。
4. 必须对比说明为什么 fallback 能捕获 diagnostic compare args，而 sidecar hook observation 不能。
```

## 7. Tests

至少必须运行并记录：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_lhs_last_writer_provenance.py reverse_agent\strategies\compare_aware_search.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "compare_lhs_last_writer or compare_real_lhs_last_writer or hooks_installed or pre_compare_handoff"
python -m pytest -q tests\test_compare_aware_search_strategy.py
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
```

如果修改 `compare_pre_compare_handoff_target_probe.py`，额外运行：

```powershell
python -m py_compile reverse_agent\olly_scripts\compare_pre_compare_handoff_target_probe.py
```

必须新增或更新测试覆盖：

```text
1. script.on('message') 在 script.load() 前注册；测试不能允许 hooks_installed ack 因时序丢失。
2. JS hooks_installed message 被 Python message handler 记录为 hooks_installed_stage_seen=true。
3. JS hook install exception 被记录为 hook_install_error_count>0，且不能被映射成 generic timeout。
4. per_hook_install_results 至少记录 hook name、address、status、error。
5. script_load_status=loaded 但无 hooks_installed 时，classification 不得是 SUCCESS。
6. hooks installed but no hook hit 时，classification 必须区别于 hook install failure。
7. CompareProbe fallback 不能使 runtime_backed_writer_identified 成立。
8. candidate set remains exactly two bounded candidates unless explicit fixture overrides it。
9. artifact 中必须保留 subprocess health 字段，不回退上一轮 lifecycle observability。
```

如果 runtime 环境可用，必须重新跑 bounded sidecar，并记录：

```text
run_name
candidate_inputs_hex
subprocess_command
subprocess_cwd
subprocess_returncode
subprocess_timeout_seconds
subprocess_timed_out
scripted_lifecycle_entered
scripted_last_runtime_stage
script_load_status
spawn_attach_resume_status
ui_trigger_status
js_top_level_seen
js_hooks_install_begin_seen
js_hooks_installed_seen
python_message_count_total
per_hook_install_results
hook_install_status
hooks_installed_stage_seen
hooks_installed_stage_hook_count
same_process_compare_args_captured
diagnostic_compare_args_captured
compare_probe_fallback_used
compare_probe_fallback_is_provenance=false
runtime_backed_writer_identified
root_cause_hypothesis
root_cause_evidence
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260523_samplereverse_sidecar_hooks_installed_observation_blocker
```

注意：

```text
如果仍无法观察 hooks_installed 或 hook_install_error，report.status 必须是 BLOCKED 或 PARTIAL，不得是 SUCCESS。
如果只是 hook points 未命中，但 hooks_installed 已确认，可写 PARTIAL，并给出下一步 bounded hook correction。
如果识别出 runtime-backed writer，必须提供 same-process、same-run、same-candidate 的 evidence，不得引用 fallback diagnostic address。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 仍然没有 hooks_installed 或 hook_install_error，且不能解释 JS/Python message bridge 是否工作。
2. 无法记录 js_top_level_seen、python_message_count_total、per_hook_install_results。
3. 需要靠扩大 timeout 才能推进。
4. 需要回旧 sample_solver。
5. 需要运行 Base64/RC4 breakpoint probe。
6. 需要把 stale artifact 当作 current evidence。
7. 需要手动编辑 task_packet.json / current_state.json / artifact_index.json / negative_results.json。
8. 需要读取或提交完整 solve_reports。
9. 需要使用 compare_semantics_agree=false candidate 作为主线。
10. 需要把 CompareProbe fallback 当成 provenance。
11. 无法让 report.based_on_decision_id 绑定当前 decision_id。
12. 无法让 pytest_result.txt 记录真实测试和 runtime/blocked 状态。
13. 需要继续写 PROJECT_PROGRESS_LOG.txt。
14. 需要引入重型 workflow/runtime 依赖。
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary 存在，based_on_decision_id 指向 decision_20260523_samplereverse_sidecar_hooks_installed_observation_blocker。
2. report.status 不得在无 hooks_installed / 无 hook_install_error / 无 hook observation 时写 SUCCESS。
3. artifact 明确记录 JS top-level、hooks_install_begin、hooks_installed、message callback、per-hook install result。
4. 当前 blocker 必须从 hooks_installed_stage_missing_after_script_load 进一步收窄。
5. 如果 hooks installed 但 hook 未命中，必须明确 classification 为 hook_not_hit，而不是 generic timeout。
6. 如果 hook install error，必须记录异常消息、hook name、address。
7. CompareProbe fallback 仍为 diagnostic-only，compare_probe_fallback_is_provenance=false。
8. 不破坏 subprocess health 和 lifecycle fields。
9. 不修改 PROJECT_PROGRESS_LOG.txt。
10. 不手动修改 task_packet/current_state/artifact_index/negative_results。
11. 不运行 Base64/RC4 breakpoint probe。
12. 不回旧 solver 或扩大搜索。
13. 保持两个 bounded candidates，不新增候选搜索。
14. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
15. 不提交完整 solve_reports。
```

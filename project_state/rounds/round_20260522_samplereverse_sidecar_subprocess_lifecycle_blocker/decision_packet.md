```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_samplereverse_sidecar_subprocess_lifecycle_blocker_20260522",
  "round_id": "round_20260522_samplereverse_sidecar_subprocess_lifecycle_blocker",
  "based_on_state_build_id": "state_20260520_052928_8a77e6637c6c",
  "based_on_state_digest": "8a77e6637c6cf7578750af01b447ccf7c39541df00661e8c882bc89cd826339d",
  "status": "APPROVED"
}
```

# DECISION_PACKET

本轮继续 `samplereverse` 逆向解题主线。

上一轮 `report_samplereverse_sidecar_hook_install_message_error_audit_20260522` 的 Codex 报告结论是可信的 `BLOCKED / REWORK_REQUIRED`：它没有把 runtime 失败伪装成成功，并且代码层面已经把 Frida message error、Python exception、hook-install error、`hooks_installed_stage_seen`、`per_hook_install_results` 等观测字段拆开。但 runtime 证据仍然阻断：bounded sidecar subprocess 没有推进到 `script_load_status=loading/loaded`，只留下 initial `not_started` payload。

本轮目标不是继续扩展 hook-install 字段，也不是推进候选搜索，而是定位为什么 sidecar subprocess 没有进入 Frida/script lifecycle。必须解释 subprocess 是否真实启动、命令行是否正确、stdout/stderr/returncode/TimeoutExpired 是否记录充分、为什么 CompareProbe fallback 仍能执行而 sidecar 停在 `not_started`。

## 1. Goal

本轮目标：

```text
1. 定位 compare_lhs_last_writer sidecar subprocess 为什么只写 initial payload，未进入 script lifecycle。
2. 审计 subprocess command、cwd、target path、out_path、probe_hex、per-probe timeout、stdout/stderr、returncode、TimeoutExpired 捕获逻辑。
3. 审计 compare_pre_compare_handoff_target_probe.py 在 main() 入口早期是否可能因参数、target、Frida import、spawn、权限、路径、window attach 前异常而未更新 artifact。
4. 审计 compare_aware_search.py 如何判断 scripted_output_exists、如何读取 compare_out、如何写 compare_log，是否在 timeout 场景下丢失关键 stdout/stderr。
5. 对比 CompareProbe fallback 为什么仍能捕获 diagnostic compare args，而 sidecar subprocess 不能推进到 lifecycle。
6. 审计 round_manifest.source_git_commit 为什么仍是旧值 593499f29508；必要时修复 archive provenance，但不要改 project_state schema。
7. 保持 two-candidate bounded scope；不新增候选，不扩大 beam/budget/topN/frontier iteration，不运行 Base64/RC4 breakpoint probe。
```

最低可接受推进：

```text
A. 明确解释 sidecar subprocess 停在 not_started 的直接原因，或给出 BLOCKED 且说明缺失的最小日志/环境条件。
B. runtime artifact 或 pytest_result 必须记录 command、returncode、stdout/stderr 摘要、scripted_output_exists、compare_out_modified/size、compare_log path。
C. 如果只是 timeout，必须说明 timeout 发生在 Python script 的哪个阶段，而不是泛写 timeout_before_script_lifecycle_observation。
D. 如果无法判断 subprocess 是否真实进入 main()，report.status 必须是 BLOCKED，不能写 SUCCESS 或 ACCEPTED。
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
run_name = sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1
classification = instrumentation_incomplete
instrumentation_failure_stage = timeout_before_script_lifecycle_observation
root_cause_hypothesis = timeout_before_script_lifecycle_observation
hook_install_status = not_confirmed_stage_missing
hook_count = 0
requested_hook_count = 3
hooks_installed_stage_seen = false
hooks_installed_stage_hook_count = 0
hook_install_error_count = 0
frida_message_error_count = 0
python_exception_count = 0
script_load_status = not_started
script_load_error = empty
spawn_attach_resume_status = not_started
ui_trigger_status = not_started
same_process_compare_args_captured = false
diagnostic_compare_args_captured = true
compare_probe_fallback_used = true
compare_probe_fallback_is_provenance = false
runtime_backed_writer_identified = false
project_progress_log_handling = untouched
```

上一轮审计结论：

```text
BLOCKED

原因：
1. report 与 decision_id 匹配，且 Codex 正确标为 BLOCKED / REWORK_REQUIRED。
2. 代码层面完成了 Frida/Python/hook-install error 分离和 per-hook install result 字段。
3. 但 runtime 没有推进到 hook install 生命周期，停在 not_started。
4. 本轮 sidecar artifact 不在 artifact_index.latest_artifacts_v2 current 范围内，不能当作 live indexed current evidence。
5. round_manifest.source_git_commit 仍是旧值 593499f29508，archive provenance 可疑。
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
不要继续只加 artifact 字段而不解释 subprocess 为什么没进入 lifecycle。
不要靠扩大 timeout 当作主要推进方式。
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
project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/round_manifest.json
project_state/rounds/round_20260522_samplereverse_sidecar_hook_install_message_error_audit/git_diff.patch
reverse_agent/strategies/compare_aware_search.py
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

允许有界读取上一轮 sidecar artifacts/logs，但不得扫描完整 `solve_reports/`：

```text
solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/compare_lhs_last_writer_provenance_audit.json
solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.json
solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c1.log
solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.json
solve_reports/harness_runs/sr_lhs_last_writer_hook_install_message_error_audit_20260522_r1/reports/tool_artifacts/samplereverse_patched/compare_lhs_last_writer_provenance_audit/c2.log
```

如果上述 artifact/log 本地不存在，不要扫描完整 `solve_reports/`；报告 `BLOCKED`，或者重新运行 bounded sidecar 并说明缺失路径。

## 5. Required Audit

实现前必须在 `project_state/codex_execution_report.md` 中说明：

```text
1. 当前 decision_id、state_build_id、state_digest。
2. 为什么上一轮是 BLOCKED，而不是 ACCEPTED。
3. compare_aware_search.py 构造的 subprocess command 完整内容，包括 Python executable、script path、target、probe_hex、out_path、timeout 参数。
4. subprocess cwd/env 是否与 CompareProbe fallback 一致，尤其是 PATH、working directory、target path、Frida/pywinauto 可用性。
5. TimeoutExpired 捕获后 stdout/stderr 是否完整写入 compare_log。
6. compare_out 是否只包含 initial payload；如是，说明 initial payload 写入时间和后续没有覆盖的原因假设。
7. scripted_output_exists、compare_out.stat().st_size、compare_log.stat().st_size、returncode、stdout/stderr 摘要是否进入 candidate health 或 report。
8. compare_pre_compare_handoff_target_probe.py 在 frida.spawn 前有哪些可能阻断：参数解析、target exists、output dir、import frida、import pywinauto、candidate decode、权限。
9. 如果 subprocess 进入 main() 并写 initial payload，为什么 runtime_stage 没从 script_started 进入 spawning_target；是否是 initial write 后卡在 import、target resolve、spawn、attach、权限、或 GUI 环境。
10. CompareProbe fallback 的调用路径和 sidecar 调用路径有哪些差异，为什么 fallback 能捕获 diagnostic compare args。
11. round_manifest.source_git_commit 为什么仍是 593499f29508；archive-round 是否使用了错误的 commit source，是否能用现有字段/命令修正。
12. 本轮是否需要重建 project_state；如需要只能运行 project_state build/status，不得手动编辑 state JSON。
```

## 6. Implementation Scope

允许修改：

```text
reverse_agent/strategies/compare_aware_search.py
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
tests/test_compare_aware_search_strategy.py
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

只有确认为必要时，才允许小幅修改：

```text
reverse_agent/project_state.py
```

修改 `reverse_agent/project_state.py` 仅限于修复 `archive-round` 的 `source_git_commit` provenance，不得改 schema，不得引入新 workflow runtime。

不要修改：

```text
PROJECT_PROGRESS_LOG.txt
reverse_agent/harness.py
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/schema.md
docs/phase2_harness_reproducibility_completion.md
```

必须新增或保证输出：

```text
subprocess_command
subprocess_cwd
subprocess_returncode
subprocess_timeout_seconds
subprocess_timed_out
subprocess_stdout_tail
subprocess_stderr_tail
scripted_output_exists
scripted_output_size_bytes
scripted_output_mtime
scripted_log_path
scripted_log_size_bytes
scripted_initial_payload_only
scripted_lifecycle_entered
scripted_last_runtime_stage
compare_probe_fallback_command_or_path
compare_probe_sidecar_invocation_diff
```

### 6.1 Required sidecar behavior

sidecar scope 必须保持 bounded：

```text
compare site: 0x258c
post_handoff_lhs_reload: 0x2559
bounded helper candidate: 0x1b50
candidate 1: 78d540b49c59077041414141414141
candidate 2: 5a3e7f46ddd474d041414141
```

必须做到以下之一：

```text
A. 解释 subprocess 为什么停在 initial payload / not_started，并给出可执行 root cause。
B. 修复 subprocess lifecycle，使 sidecar 至少推进到 spawning_target / attaching_frida / loading_script，并记录后续阻断点。
C. 如果环境无法运行，明确 BLOCKED，并说明需要的最小本地环境信息或日志。
```

如果使用 CompareProbe fallback：

```text
1. fallback 只能填充 diagnostic fields。
2. artifact 必须包含 compare_probe_fallback_is_provenance = false。
3. 不能把 fallback arg0 地址与另一进程/另一 run 的 write events 关联成 runtime-backed writer。
4. 必须对比说明为什么 fallback 可观察而 sidecar 不可观察。
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

如果修改 `reverse_agent/project_state.py`，额外运行：

```powershell
python -m py_compile reverse_agent\project_state.py
python -m pytest -q tests\test_project_state.py
```

必须新增或更新测试覆盖：

```text
1. TimeoutExpired 时 stdout/stderr tail 被写入 candidate health 或 artifact。
2. compare_out 只包含 initial payload 时，classification/root_cause 映射到 timeout_before_script_lifecycle_observation，并带 scripted_initial_payload_only=true。
3. subprocess command/cwd/returncode/timeout/log path 被记录。
4. compare_log 写失败时 fallback log path 被记录。
5. CompareProbe fallback 不能使 runtime_backed_last_writer_identified 成立。
6. candidate set remains exactly two bounded candidates unless explicit fixture overrides it。
7. 如修改 archive provenance，测试 round_manifest.source_git_commit 不应固定旧值。
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
subprocess_stdout_tail
subprocess_stderr_tail
scripted_output_exists
scripted_output_size_bytes
scripted_initial_payload_only
scripted_lifecycle_entered
scripted_last_runtime_stage
script_load_status
spawn_attach_resume_status
ui_trigger_status
hooks_installed_stage_seen
same_process_compare_args_captured
diagnostic_compare_args_captured
compare_probe_fallback_used
compare_probe_fallback_is_provenance=false
root_cause_hypothesis
root_cause_evidence
```

完成 report 写入后，还必须运行并记录：

```powershell
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state lint-handoff --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260522_samplereverse_sidecar_subprocess_lifecycle_blocker
```

注意：

```text
如果仍无法确认 subprocess 进入 lifecycle，report.status 必须是 BLOCKED 或 PARTIAL，不得是 SUCCESS。
如果关键 artifact/log 缺失导致无法判断，report.status 必须是 BLOCKED。
```

## 8. Stop Conditions

遇到以下情况必须停止并报告：

```text
1. 仍只能得到 not_started，但不能解释 subprocess 是否实际启动。
2. 无法记录 subprocess command、returncode、stdout/stderr、compare_out/log 状态。
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
```

## Acceptance Criteria

本轮可接受条件：

```text
1. codex_report_summary 存在，based_on_decision_id 指向 decision_samplereverse_sidecar_subprocess_lifecycle_blocker_20260522。
2. report.status 不得在 sidecar lifecycle 未进入时写 SUCCESS。
3. subprocess command/cwd/returncode/timeout/stdout/stderr/log/artifact 状态被记录。
4. scripted_initial_payload_only 与 scripted_lifecycle_entered 被明确记录。
5. 如果 sidecar 仍失败，root_cause_evidence 必须比 timeout_before_script_lifecycle_observation 更具体。
6. CompareProbe fallback 仍为 diagnostic-only，compare_probe_fallback_is_provenance=false。
7. 不破坏 PROJECT_PROGRESS_LOG.txt revert，且不再修改 PROJECT_PROGRESS_LOG.txt。
8. 没有手动修改 task_packet/current_state/artifact_index/negative_results。
9. 没有运行 Base64/RC4 breakpoint probe。
10. 没有回旧 solver 或扩大搜索。
11. 保持两个 bounded candidates，不新增候选搜索。
12. tests / py_compile / lint-decision / lint-report / lint-handoff / archive-round 被真实记录。
13. 不提交完整 solve_reports。
14. 如修复 archive provenance，round_manifest.source_git_commit 不应继续固定到旧的 593499f29508。
```

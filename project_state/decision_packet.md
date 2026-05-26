```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260526_reverse_arg0_ui_trigger_timing_validation",
  "round_id": "round_20260526_reverse_arg0_ui_trigger_timing_validation",
  "based_on_state_build_id": "state_20260526_080937_c7583ea6dc32",
  "based_on_state_digest": "c7583ea6dc3287378a856af210a6f00853908844427ad5673fa0d652872faac9",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **逆向解题主线**，不是工程架构改造支线。当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`，不是 `project_state/task_packet.json` 中的 `task` 或 `derived_task`。

上一轮审计结论为 **ACCEPTED_WITH_LIMITATIONS**：Codex 已把 blocker 从 `arg0_final_writer_trace_schema_gap` 细化为 `arg0_ui_trigger_or_timeout_blocked`，核心任务完成；限制是报告中的 `files_changed` 未列出新增 round archive 文件，且报告中的 archive 状态是 pre-archive 视角。这些限制不阻断下一轮，但本轮报告必须避免类似时序不一致。

## 1. Goal

本轮目标：验证并修复 `compare_real_lhs_provenance_audit` sidecar 中的 **UI trigger timing path**。

当前 blocker 是：

```text
arg0_ui_trigger_or_timeout_blocked
```

本轮必须回答并落地：

```text
1. UI/input trigger 为什么显示为 button_triggered 但 ui_trigger_after_hooks_installed=false。
2. 这是实际时序错误、telemetry 记录错误、还是 timeout/等待屏障错误。
3. hooks installed event 是否真的先于 UI trigger 完成。
4. Python message callback 是否仍保证在 script.load 前注册。
5. sidecar 是否需要 hooks_installed readiness barrier，且不能扩大全局 timeout/budget。
6. 修复后是否能产生 post-ui observation，或者能更准确地区分 hook_not_hit 与 timeout_blocked。
```

本轮不追 final writer，不做 candidate search，不扩大 frontier，不进入 Base64/RC4 probe。只有在最小代码修复后需要验证时，允许一次 bounded rerun。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 state 基础：

```text
state_build_id = state_20260525_161438_9a1014f18931
state_digest = 9a1014f18931ac3ab635b4813e692f4d967346df92d0cab8b2a03c33d3ec67e8
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = inconclusive
current_bottleneck.blocker = arg0_ui_trigger_or_timeout_blocked
```

`task_packet.task` / `task_packet.derived_task` 当前只是派生建议。当前轮执行权威是本 `project_state/decision_packet.md`。

当前 selected run：

```text
selected run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.run_manifest.freshness = current
latest_artifacts_v2.summary.freshness = current
latest_artifacts_v2.compare_probe.freshness = stale
```

上一轮有效结论：

```text
process_spawned = yes
frida_attached = yes
script_loaded = loaded
callback_before_load = true
hooks_installed = installed
hook_count = 4
hook_install_error_count = 0
ui_trigger_status = button_triggered
ui_trigger_after_hooks_installed = false
python_message_count_total > 0
observation_count = 0
post_ui_observation_count = 0
hook_hits = none
final_blocker_classification = arg0_ui_trigger_or_timeout_blocked
```

固定 candidates：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

固定 hook points：

```text
module+0x253a old_lhs_slot_store
module+0x2559 post_handoff_lhs_reload
module+0x258b pre_compare_lhs_push
module+0x258c static_compare_callsite
```

当前风险：

```text
compare_probe 是 stale，不能当作 current evidence。
fallback-only 0x258c 不能当作 runtime-backed actual arg0。
hook installed 不能等于 hook hit。
ui_trigger_after_hooks_installed=false 可能是实际触发早于 hook install，也可能是 telemetry timestamp/ordering bug。
当前不能继续追 final writer，必须先修复或验证 UI trigger timing path。
```

当前 skill_profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

## 3. Do Not Do

不要做以下事情：

```text
不要继续工程支线或 skill 改造。
不要修改 .codex-skills/、registry、sync 或 audit 工具。
不要默认读取完整 solve_reports/。
不要默认读取 PROJECT_PROGRESS_LOG.txt。
不要运行 Base64/RC4 breakpoint probe。
不要运行 Base64/RC4 probe 的任何变体。
不要回 old sample_solver blind search。
不要扩大 beam / topN / budget / timeout / frontier iteration。
不要新增 candidate search。
不要把 compare_semantics_agree=false candidates 作为 primary frontier。
不要提交完整 solve_reports。
不要把 stale / missing artifact 当 current evidence。
不要把 stale compare_probe 当 current compare evidence。
不要把 compare_probe fallback args 当 writer provenance。
不要把 fallback-only 0x258c 当 runtime-backed actual arg0。
不要把 hook installed 当作 hook hit。
不要把 pointer carrier 伪称为 final data writer。
不要把 slot pointer write 伪称为 buffer data write。
不要无条件复用旧 [ebp-0x1170] 作为真实 LHS source。
不要把 0x4019e0、0x401b50、0x4018cd、0x401be3 直接称为 Base64/RC4 producer，除非本轮产生新的 runtime-backed 语义证据。
不要为了推进而伪造 final writer。
不要在 UI trigger timing 未解释前再次尝试 writer provenance claim。
不要通过扩大 timeout/budget 掩盖时序 bug。
```

必须遵守 `project_state/negative_results.json`，尤其是：

```text
old sample_solver blind search
only increase guided_pool beam or budget
use compare_semantics_agree=false candidates as primary frontier
commit full solve_reports directory
rerun Base64/RC4 breakpoint probe before confirming a Base64/RC4 instruction hook
repeat producer material confirmation without adding instruction-level evidence
reuse old [ebp-0x1170] without real-lhs provenance evidence
run Base64/RC4 breakpoint probe before real lhs producer identification
```

## 4. Files To Inspect

必须读取：

```text
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/codex_execution_report.md
project_state/decision_packet.md
project_state/pytest_result.txt
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

必须有界读取 current selected run artifacts：

```text
solve_reports/harness_runs/sr_arg0_bounded_writer_trace_20260525_r1/run_manifest.json
solve_reports/harness_runs/sr_arg0_bounded_writer_trace_20260525_r1/summary.json
solve_reports/harness_runs/sr_arg0_bounded_writer_trace_20260525_r1/case_results/samplereverse-compare-producer-backtrace.json
solve_reports/harness_runs/sr_arg0_bounded_writer_trace_20260525_r1/reports/tool_artifacts/samplereverse_patched/compare_real_lhs_provenance_audit/compare_real_lhs_provenance_audit.json
```

允许有界读取：

```text
sr_arg0_bounded_writer_trace_20260525_r1 下 candidate_1/candidate_2/candidate_3 的 compare_real_lhs_provenance_audit.json
当前 sidecar 生成的 per-candidate output json
```

不要默认读取：

```text
完整 solve_reports/
完整 PROJECT_PROGRESS_LOG.txt
历史 rounds 下的完整大文件
.codex-skills/**
```

## 5. Required Audit

Codex 修改前必须在 report 中记录：

```text
1. 确认本 decision_id=decision_20260526_reverse_arg0_ui_trigger_timing_validation。
2. 确认 mainline=reverse_solving，skill_profiles 为 reverse-agent-iteration@v2 与 samplereverse-frontier@v2。
3. 确认 task_packet.task / derived_task 只是派生建议，当前执行权威是 decision_packet.md。
4. 确认 selected run 是 sr_arg0_bounded_writer_trace_20260525_r1。
5. 确认 compare_real_lhs_provenance_audit freshness=current。
6. 确认 compare_probe freshness=stale，不能当 current evidence。
7. 确认上一轮 blocker 已是 arg0_ui_trigger_or_timeout_blocked，而不是 schema_gap。
8. 确认本轮目标不是 final writer，而是 UI trigger timing path。
9. 确认本轮没有 Base64/RC4 probe、old solver、candidate search、beam/budget/timeout/frontier 扩张。
```

必须输出 UI timing diagnosis table：

```text
candidate_hex
process_spawned
frida_attached
script_loaded
message_callback_registered_before_load
hooks_install_begin_seen
hooks_installed_seen
hook_count
hook_install_error_count
hooks_installed_timestamp_ms
ui_trigger_start_timestamp_ms
ui_trigger_end_timestamp_ms
ui_trigger_status
ui_trigger_after_hooks_installed
python_message_count_total
python_message_count_by_type
observation_count
post_ui_observation_count
hook_hit_counts_by_name
first_observation_timestamp_ms
last_observation_timestamp_ms
timeout_or_wait_reason
root_cause_classification
```

必须明确区分：

```text
actual_ordering_bug
telemetry_ordering_bug
hooks_ready_barrier_missing
ui_trigger_timeout_or_window_too_early
target_path_or_process_mismatch
still_runtime_blocked
```

## 6. Implementation Scope

### Phase A：只读诊断

先不改代码，先读取 current selected run 的 artifact，判断已有字段是否足够解释：

```text
hooks installed 是否真的有 timestamp。
UI trigger 是否真的发生在 hooks installed 前。
ui_trigger_after_hooks_installed=false 是否由 timestamp 缺失、默认值、字段名不一致或 event 顺序造成。
Python callback 是否在 script.load 前注册。
已有 python_message_count 是否证明 message bridge 正常。
```

如果已有字段已经足够证明只是 projection/telemetry ordering bug，优先只修改 projection 或 telemetry 字段解释，不做 runtime rerun。

### Phase B：最小 sidecar timing 修补

如果字段不足或代码确实存在顺序问题，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

允许新增/修正字段：

```text
process_spawned_at_ms
frida_attached_at_ms
script_load_start_at_ms
script_loaded_at_ms
message_callback_registered_at_ms
hooks_install_begin_at_ms
hooks_installed_at_ms
ui_trigger_start_at_ms
ui_trigger_end_at_ms
first_python_message_at_ms
last_python_message_at_ms
first_observation_at_ms
last_observation_at_ms
hooks_ready_barrier_seen
hooks_ready_barrier_wait_ms
hooks_ready_before_ui_trigger
ui_trigger_after_hooks_installed
ui_trigger_timing_status
timeout_or_wait_reason
root_cause_classification
root_cause_evidence
```

必须保证：

```text
message callback 注册仍在 script.load 前。
UI trigger 必须等待 hooks_installed / hooks_ready event，等待必须在现有 bounded runtime window 内完成，不允许通过扩大 timeout/budget 解决。
hook_install_status=installed 只说明 attach/install 成功，不等于 hook hit。
observation_count=0 时不能投影为 final writer schema_gap。
fallback-only compare_probe 不能提供 actual_arg0 runtime-backed evidence。
stale compare_probe 不能成为 current evidence。
```

### Phase C：classification projection

必须把 UI timing path 分类为以下之一：

```text
arg0_ui_trigger_timing_fixed_observations_available
arg0_hooks_ready_but_not_hit
arg0_hooks_ready_message_delivery_failed
arg0_ui_trigger_barrier_missing_fixed
arg0_ui_trigger_timing_telemetry_bug_fixed
arg0_ui_trigger_or_timeout_blocked
arg0_target_path_or_process_mismatch
arg0_writer_trace_runtime_blocked
```

分类建议：

```text
arg0_ui_trigger_timing_fixed_observations_available:
- hooks ready before UI trigger；
- post-ui observation_count > 0；
- 可继续进入下一轮 final writer provenance。

arg0_hooks_ready_but_not_hit:
- hooks ready before UI trigger；
- UI triggered；
- message bridge normal；
- observation_count == 0；
- hook_hit_counts_by_name 全为 0。

arg0_hooks_ready_message_delivery_failed:
- hook hit counter 增加；
- Python observation message 缺失或 decode/message error 存在。

arg0_ui_trigger_barrier_missing_fixed:
- 原代码确实 UI trigger 早于 hooks ready；
- 已加入 readiness barrier；
- rerun 尚无 observation，但 root cause 已确认。

arg0_ui_trigger_timing_telemetry_bug_fixed:
- 实际顺序正确；
- 旧字段为 false 是 timestamp/field projection bug；
- 已修正 telemetry/projection。

arg0_ui_trigger_or_timeout_blocked:
- hooks installed；
- UI trigger 未完成、未能证明发生在 hooks ready 之后，或 existing timeout/window 内无法进入目标路径。
```

### Phase D：是否允许 rerun

默认不 rerun。只有在 timing 修补后必须验证字段时，允许一次 bounded rerun，run-name 必须为：

```text
sr_arg0_ui_trigger_timing_20260526_r1
```

限制：

```text
只用同三个 fixed candidates。
只用 0x253a / 0x2559 / 0x258b / 0x258c。
不得扩大 candidate、beam、topN、budget、timeout、frontier。
不得运行 Base64/RC4 probe。
不得提交完整 solve_reports。
```

如果不 rerun，必须说明为何已有 artifact 或单元测试足够支持分类。

### Phase E：状态、报告与归档

必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

如果修改 projection 或 rerun，必须运行 project_state build：

```bash
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
```

报告必须明确说明：

```text
当前是否仍使用 sr_arg0_bounded_writer_trace_20260525_r1。
是否生成新 runtime artifact。
如果生成新 run，run-name 是否为 sr_arg0_ui_trigger_timing_20260526_r1。
UI trigger timing root cause 是实际时序问题、telemetry bug、barrier 缺失、timeout/window 问题，还是仍 blocked。
是否允许下一轮回到 actual arg0 final writer provenance。
```

若执行 archive-round，必须在 `codex_report_summary.files_changed` 中列出新增/修改的 round archive 文件，避免上一轮的 report/final repository 状态轻微不一致。

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or hook or timeout or observation or ui or trigger or timing or classification"
python -m pytest -q tests/test_project_state.py -k "sidecar or ui or trigger or timing or observation or blocker or report or runtime"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name <selected_or_new_run_name>
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

如果修改了 `reverse_agent/project_state.py`，必须补充：

```bash
python -m pytest -q tests/test_project_state.py
```

如果修改了 sidecar timing/telemetry，必须补充 fixture/unit tests，覆盖：

```text
UI trigger 早于 hooks ready 能被分类为 arg0_ui_trigger_or_timeout_blocked 或 barrier_missing_fixed。
hooks ready before UI trigger 且 zero observations 能被分类为 arg0_hooks_ready_but_not_hit。
hook hit but Python message missing/error 能被分类为 arg0_hooks_ready_message_delivery_failed。
telemetry timestamp 字段缺失时不能误报为 final writer schema_gap。
fallback-only compare_probe 不能变成 runtime-backed actual arg0。
stale compare_probe 不能被 current_state 当 current evidence。
```

不需要运行：

```text
full unrelated pytest suite
Base64/RC4 breakpoint probe
old sample_solver
full solve_reports scan
PROJECT_PROGRESS_LOG read
```

## 8. Stop Conditions

遇到以下情况必须停止并报告，不要硬改：

```text
1. 必须扩大 timeout/budget/frontier 才能继续。
2. 必须运行 Base64/RC4 probe 才能继续。
3. 必须回 old solver 才能继续。
4. 必须读取完整 solve_reports 或 PROJECT_PROGRESS_LOG.txt 才能继续。
5. 不能区分 actual ordering bug、telemetry ordering bug、barrier missing、timeout/window blocked。
6. 只能得到 fallback compare_probe，无法得到 scripted sidecar evidence。
7. 需要修改 .codex-skills 或 registry 才能继续。
8. 测试无法运行且没有记录环境原因。
9. 代码会把 stale compare_probe 当 current evidence。
10. 代码会把 fallback-only compare evidence 当 runtime-backed actual arg0。
11. 代码会把 UI timing blocker 重新压回 arg0_final_writer_trace_schema_gap。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260526_reverse_arg0_ui_trigger_timing_validation",
  "round_id": "round_20260526_reverse_arg0_ui_trigger_timing_validation",
  "based_on_decision_id": "decision_20260526_reverse_arg0_ui_trigger_timing_validation",
  "status": "SUCCESS / PARTIAL / FAILED / BLOCKED",
  "acceptance_recommendation": "ACCEPTED / NEEDS_REVIEW / REWORK_REQUIRED / BLOCKED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": [],
  "next_suggested_task": []
}
```

报告正文必须包含：

```text
1. current selected run / artifact freshness。
2. stale compare_probe 风险说明。
3. UI timing diagnosis table。
4. hooks ready / UI trigger / message delivery / hook hit / observation 区分结论。
5. 是否 rerun；如果 rerun，run-name 和命令。
6. 新 current_bottleneck.blocker。
7. 是否允许下一轮回到 actual arg0 final writer provenance。
8. 真实测试命令和结果。
9. git diff --stat 摘要。
10. 若 archive-round，必须列出 archive 文件并说明 included_diff / included_state_snapshot 状态。
```

验收标准：

```text
ACCEPTED：
- 明确解释 ui_trigger_after_hooks_installed=false 的根因。
- 修复或准确分类 UI trigger timing path。
- 没有 stale evidence misuse。
- 没有 fallback-only actual_arg0 误用。
- 没有把 hook installed 当 hook hit。
- 没有把 UI timing blocker 重新压成 final writer schema_gap。
- tests/lints 通过。

ACCEPTED_WITH_LIMITATIONS：
- 能把 root cause 缩小到 barrier/timing/telemetry/timeout 之一，但还不能产生 post-ui observations。
- 后续任务可以据此做一次更小的 sidecar runtime validation 或进入 hook-not-hit 解释。

REWORK_REQUIRED：
- 继续把 installed-but-no-observation 或 UI timing blocker 归为 schema_gap。
- 把 fallback-only compare evidence 当成 runtime-backed actual_arg0。
- 未解释 ui_trigger_after_hooks_installed=false。
- report/decision/pytest id mismatch。
- archive 文件与 files_changed 明显不一致。

BLOCKED：
- runtime 环境不可用。
- current artifact 缺失且无法 rebuild。
- 必要测试无法运行。
```

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260525_reverse_arg0_sidecar_observation_blocker_fix",
  "round_id": "round_20260525_reverse_arg0_sidecar_observation_blocker_fix",
  "based_on_state_build_id": "state_20260525_150911_78117fa9b052",
  "based_on_state_digest": "78117fa9b052e0908bbd18bcd1a1a6ecb4ecc2d9a3a383baa6d4f8d74b1fb64f",
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

上一轮审计结论为 **REWORK_REQUIRED**。Codex 确实执行了 bounded rerun 并生成了新 run `sr_arg0_bounded_writer_trace_20260525_r1`，但四个目标 hook 点没有产生有效 runtime observation rows，`0x258c` 也只是 fallback-only，且没有 actual `arg0` value。当前不能继续追 final data writer；必须先修复或定位 sidecar observation delivery blocker。

## 1. Goal

本轮目标：修复或定位 `sr_arg0_bounded_writer_trace_20260525_r1` 中的 sidecar observation delivery blocker。目标不是继续追 final writer，而是解释为什么四个 hooks 安装成功却没有任何 observation rows。

必须把 current blocker 从笼统的 `arg0_final_writer_trace_schema_gap` 细化为以下之一：

```text
arg0_writer_trace_runtime_blocked
arg0_hook_installed_but_not_hit
arg0_hook_hit_but_message_delivery_failed
arg0_ui_trigger_or_timeout_blocked
arg0_target_path_or_process_mismatch
```

必须回答：

```text
1. 目标进程是否真的启动并触发 UI/input。
2. Frida script 是否 load 成功。
3. Python message callback 是否注册在 script.load 前。
4. hook_install_status=installed 是否对应真实地址。
5. hook hit count 是否为 0，还是 message delivery 丢失。
6. timeout 是否过短导致 UI 还没走到 0x253a/0x2559/0x258b/0x258c。
7. fallback compare_probe 为什么能跑，但 scripted hooks 没有 observation。
8. selected target path 是否是正确 patched exe。
9. 当前应该分类为 runtime_blocked、hook_not_hit、message_delivery_failed、timeout_blocked 还是 target/process mismatch。
```

本轮不求 final writer，不做 candidate search，不扩大 frontier，不扩大 runtime budget，不进入 Base64/RC4 probe。

## 2. Current Evidence

当前主线：**reverse_solving**。

当前 state 基础：

```text
state_build_id = state_20260525_150911_78117fa9b052
state_digest = 78117fa9b052e0908bbd18bcd1a1a6ecb4ecc2d9a3a383baa6d4f8d74b1fb64f
profile = samplereverse
active_strategy = CompareAwareSearchStrategy
current_bottleneck.stage = compare_real_lhs_provenance_audit
current_bottleneck.reason = inconclusive
current_bottleneck.blocker = arg0_final_writer_trace_schema_gap
```

`task_packet.task` / `task_packet.derived_task` 当前只是派生建议。当前轮执行权威是本 `project_state/decision_packet.md`。

当前 selected run：

```text
new run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.compare_real_lhs_provenance_audit.freshness = current
latest_artifacts_v2.compare_real_lhs_provenance_audit.source_run = sr_arg0_bounded_writer_trace_20260525_r1
latest_artifacts_v2.run_manifest.freshness = current
latest_artifacts_v2.summary.freshness = current
latest_artifacts_v2.compare_probe.freshness = stale
```

上一轮 report 关键事实：

```text
0x253a old_lhs_slot_store = missing
0x2559 post_handoff_lhs_reload = missing
0x258b pre_compare_lhs_push = missing
0x258c static_compare_callsite = fallback-only / no actual arg0 value
scripted_hook_no_observations
hook_count = 4
hook_install_status = installed
actual_arg0 = missing for all three candidates
raw_write_count = 0
intersecting_write_count = 0
final writer = missing
```

固定 candidates：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

当前风险：

```text
compare_probe 是 stale，不能当作 current evidence。
fallback-only 0x258c 不能当作 runtime-backed actual arg0。
hook installed 不能等于 hook hit。
当前 blocker 仍是 arg0_final_writer_trace_schema_gap，但实际更像 runtime observation delivery blocker。
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
不要继续把 installed-but-no-observation 归为 schema_gap。
不要在没有 observation blocker 解释前再次尝试 writer provenance claim。
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
1. 确认本 decision_id=decision_20260525_reverse_arg0_sidecar_observation_blocker_fix。
2. 确认 mainline=reverse_solving，skill_profiles 为 reverse-agent-iteration@v2 与 samplereverse-frontier@v2。
3. 确认 task_packet.task / derived_task 只是派生建议，当前执行权威是 decision_packet.md。
4. 确认 selected run 是 sr_arg0_bounded_writer_trace_20260525_r1。
5. 确认 compare_real_lhs_provenance_audit freshness=current。
6. 确认 compare_probe freshness=stale，不能当 current evidence。
7. 复核上一轮事实：hook_count=4、hook_install_status=installed、但 scripted_hook_no_observations。
8. 确认本轮目标不是 final writer，而是 sidecar observation blocker。
9. 确认本轮没有 Base64/RC4 probe、old solver、candidate search、beam/budget/timeout/frontier 扩张。
```

必须输出一个 blocker diagnosis table：

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
hook_address_by_name
ui_trigger_status
ui_trigger_after_hooks_installed
python_message_count_total
python_message_count_by_type
observation_count
hook_hit_counts_by_name
first_observation_timestamp_ms
last_observation_timestamp_ms
waiting_for_observation_reason
hook_not_hit_vs_hook_not_installed_classification
final_blocker_classification
```

## 6. Implementation Scope

### Phase A：只读诊断

先不改代码，先读取 current selected run 的 artifact，判断已有字段是否足够区分：

```text
hook installed
hook hit
message delivered
UI/input triggered
timeout before target path
process/target mismatch
script load failure
```

如果已有字段已经足够，优先只修改 projection/classification，不要重复 rerun。

### Phase B：最小 telemetry 修补

如果已有字段不足，允许最小修改：

```text
reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
```

允许新增/修正字段：

```text
process_spawned
frida_attached
script_loaded
message_callback_registered_before_load
hooks_install_begin_seen
hooks_installed_seen
hook_install_error_count
per_hook_install_results
hook_address_by_name
hook_address_validation
ui_trigger_status
ui_trigger_after_hooks_installed
script_load_to_hooks_installed_elapsed_ms
script_load_to_ui_trigger_elapsed_ms
python_message_count_total
python_message_count_by_type
observation_count
post_ui_observation_count
hook_hit_counts_by_name
first_observation_timestamp_ms
last_observation_timestamp_ms
last_observation_hook_name
waiting_for_observation_reason
hook_not_hit_vs_hook_not_installed_classification
root_cause_hypothesis
root_cause_evidence
```

必须保证：

```text
hook_install_status=installed 只说明 attach 成功，不等于 hook hit。
observation_count=0 时不能投影为 schema_gap，除非脚本字段本身缺失且不能判断。
fallback-only compare_probe 不能提供 actual_arg0 runtime-backed evidence。
stale compare_probe 不能成为 current evidence。
```

### Phase C：classification projection

必须把 current blocker 细化为以下之一：

```text
arg0_writer_trace_runtime_blocked
arg0_hook_installed_but_not_hit
arg0_hook_hit_but_message_delivery_failed
arg0_ui_trigger_or_timeout_blocked
arg0_target_path_or_process_mismatch
```

分类建议：

```text
arg0_hook_installed_but_not_hit:
- script loaded；
- hooks installed；
- hook_count == requested_hook_count；
- observation_count == 0；
- UI/input 已触发；
- 没有 message callback failure。

arg0_hook_hit_but_message_delivery_failed:
- hook hit counter 增加；
- observation message 未到 Python；
- python/frida message error 或 decode error 存在。

arg0_ui_trigger_or_timeout_blocked:
- hooks installed；
- UI trigger 未完成或 timeout 发生在 post-ui observation 前。

arg0_target_path_or_process_mismatch:
- target path 不存在/不对；
- process spawn/attach/module base 与预期不一致。

arg0_writer_trace_runtime_blocked:
- 运行链路阻断，但信息不足以进一步归因。
```

### Phase D：是否允许 rerun

默认不 rerun。只有在 telemetry 修补后必须验证字段时，允许一次 bounded rerun，run-name 必须为：

```text
sr_arg0_sidecar_observation_blocker_20260525_r1
```

限制：

```text
只用同三个 fixed candidates。
只用 0x253a / 0x2559 / 0x258b / 0x258c。
不得扩大 candidate、beam、topN、budget、timeout、frontier。
不得运行 Base64/RC4 probe。
不得提交完整 solve_reports。
```

如果不 rerun，必须说明为何已有 artifact 足够分类。

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
为什么 blocker 从 schema_gap 改为更准确 runtime blocker。
```

## 7. Tests

必须运行：

```bash
python -m py_compile reverse_agent/strategies/compare_aware_search.py reverse_agent/olly_scripts/compare_pre_compare_handoff_target_probe.py reverse_agent/project_state.py
python -m pytest -q tests/test_compare_aware_search_strategy.py -k "arg0 or hook or timeout or observation or writer or classification"
python -m pytest -q tests/test_project_state.py -k "artifact or bottleneck or report or pointer or writer or runtime"
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

如果修改了 sidecar telemetry，必须补充 fixture/unit tests，覆盖：

```text
installed-but-no-observation 不再分类为 schema_gap。
hook installed 不等于 hook hit。
fallback-only compare_probe 不能变成 runtime-backed actual arg0。
stale compare_probe 不能被 current_state 当 current evidence。
UI trigger timeout 能被投影为 arg0_ui_trigger_or_timeout_blocked。
hook hit but message missing 能被投影为 arg0_hook_hit_but_message_delivery_failed。
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
5. 不能区分 hook installed、hook hit、message delivered、UI trigger、timeout。
6. 只能得到 fallback compare_probe，无法得到 scripted sidecar evidence。
7. 需要修改 .codex-skills 或 registry 才能继续。
8. 测试无法运行且没有记录环境原因。
9. 代码会把 stale compare_probe 当 current evidence。
10. 代码会把 fallback-only compare evidence 当 runtime-backed actual arg0。
```

Codex 报告必须写入 `project_state/codex_execution_report.md`，顶部包含：

```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260525_reverse_arg0_sidecar_observation_blocker_fix",
  "round_id": "round_20260525_reverse_arg0_sidecar_observation_blocker_fix",
  "based_on_decision_id": "decision_20260525_reverse_arg0_sidecar_observation_blocker_fix",
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
3. blocker diagnosis table。
4. hook installed / hook hit / message delivery / UI trigger / timeout 区分结论。
5. 是否 rerun；如果 rerun，run-name 和命令。
6. 新 current_bottleneck.blocker。
7. 真实测试命令和结果。
8. git diff --stat 摘要。
```

验收标准：

```text
ACCEPTED：
- 明确区分 hook installed / hook hit / message delivery / UI trigger / timeout。
- current blocker 从 schema_gap 改为准确 runtime blocker。
- 没有 stale evidence misuse。
- 没有 fallback-only actual_arg0 误用。
- tests/lints 通过。

ACCEPTED_WITH_LIMITATIONS：
- 能把 blocker 缩小到 runtime_blocked，但还不能唯一归因到 hook_not_hit、message_delivery_failed、timeout 或 target mismatch。
- 后续任务可以据此做一次更小的 sidecar telemetry fix。

REWORK_REQUIRED：
- 继续把 installed-but-no-observation 归为 schema_gap。
- 把 fallback-only compare evidence 当成 runtime-backed actual arg0。
- 未解释 scripted_hook_no_observations。
- report/decision/pytest id mismatch。

BLOCKED：
- runtime 环境不可用。
- current artifact 缺失且无法 rebuild。
- 必要测试无法运行。
```

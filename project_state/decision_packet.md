```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_window_discovery_lifecycle_diagnostics",
  "round_id": "round_20260601_window_discovery_lifecycle_diagnostics",
  "based_on_state_build_id": "state_20260601_151820_67a9dc2b097f",
  "based_on_state_digest": "67a9dc2b097f537853f89e598e2f25e29ca1f1fb6a8f8ce6f4a7c334c3358290",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但只处理上一轮已经细化出的 UI runtime blocker：

```text
compare_handoff_narrower_post_entry_breakpoint_audit / window_discovery_timeout
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

本轮目标不是求最终 flag，也不是继续候选搜索；目标是把上一轮的：

```text
window_discovery_timeout
```

继续拆成可审计、可复现、可下一步行动的最小 window discovery blocker。

必须增强当前 artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit.json
```

本轮必须回答：

```text
1. window_discovery_timeout 到底发生在 app.top_window() 调用阻塞、窗口尚未创建、窗口不可见、backend 不匹配、进程已退出、窗口句柄不可枚举，还是 window inventory 为空。
2. 既然上一轮已确认 Frida spawn/attach/script load/breakpoint install/resume/ui_connect 都 OK，本轮不得回退到 spawn/attach/script/breakpoint install 诊断。
3. 每个固定候选必须记录 bounded window discovery diagnostics：pid 是否存活、pywinauto connect 是否仍可用、top_window 是否尝试、top_window 是否返回、返回的窗口 title/class/handle、窗口枚举数量、候选窗口摘要。
4. 如果 app.top_window() 卡住，必须区分 top_window_call_timeout / window_discovery_api_blocked，而不是继续笼统写 window_discovery_timeout。
5. 如果窗口枚举为空，必须输出 process_window_inventory_empty 或 process_no_visible_window。
6. 如果窗口发现成功，必须继续进入现有 input/button lookup 逻辑，但仍不得扩大到通用 GUI 自动化平台。
```

本轮的验收标准是 **window discovery blocker specificity improves**。即使目标仍不能进入 UI trigger，也必须从 `window_discovery_timeout` 细化为以下之一：

```text
process_exited_before_window_discovery
process_alive_no_top_window
process_window_inventory_empty
process_no_visible_window
top_window_call_timeout
top_window_call_failed
window_discovery_api_blocked
window_backend_mismatch
window_discovery_succeeded_input_lookup_next
window_discovery_instrumentation_gap
```

如果无法进一步细化，Codex 必须明确说明是 wrapper/sidecar window discovery instrumentation gap，并给出缺失的最小证据；不得声称成功。

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
state_build_id=state_20260601_151820_67a9dc2b097f
state_digest=67a9dc2b097f537853f89e598e2f25e29ca1f1fb6a8f8ce6f4a7c334c3358290
source_git_commit=1e15d344de99
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
workflow_status=REPORT_AVAILABLE
review_status=PENDING_REVIEW
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Review bounded narrower post-entry breakpoint audit
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

上一轮 Codex report：

```text
report_id=report_20260601_ui_trigger_lifecycle_diagnostics
based_on_decision_id=decision_20260601_ui_trigger_lifecycle_diagnostics
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
```

当前 bottleneck：

```text
stage=compare_handoff_narrower_post_entry_breakpoint_audit
reason=window_discovery_timeout
confidence=medium
```

上一轮 artifact 摘要：

```text
classification=window_discovery_timeout
candidate_count=3
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

上一轮 UI trigger evidence：

```text
last_ui_stage=ui_window_discovery_attempted
timeout_stage=window_discovery
classification=window_discovery_timeout
```

current artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit\compare_handoff_narrower_post_entry_breakpoint_audit.json
  sha256=0221eb2a46cea71964bdd97c183678c98f4d6016ffd32a05e5705366a7476e22
  size_bytes=35711
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

允许的 bounded breakpoint surface 只能保持当前范围：

```text
1. predecessor_handoff_call: module+0x2338
2. handoff_helper_entry: module+0x1b50
3. process_exception: module+0x1913, only as exception/control-flow surface
4. actual_compare: module+0x258c, only as bounded control-flow surface
```

artifact freshness 判断：

```text
1. compare_handoff_narrower_post_entry_breakpoint_audit 是 current，是本轮 blocker 的直接来源。
2. compare_handoff_post_entry_step_runtime_audit 是 current，但只作为 step_api_unavailable 背景。
3. compare_handoff_return_site_probe、function_semantic_audit、base64_rc4_static_point_discovery 等 legacy artifacts 只能作为 stale/background，不得作为新的 current runtime 证据。
4. missing artifact 不得当作 current evidence。
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
9. 不把 window discovery diagnostics 变成 material probe。
10. 不继续只输出 window_discovery_timeout 而不写窗口发现子阶段证据。
11. 不把 app.top_window timeout 当作 UI trigger 失败的充分证据；必须写出窗口枚举与进程状态。
12. 不建设通用 GUI automation framework / pywinauto adapter 平台。
13. 不默认增加 timeout 来掩盖 window discovery 缺证。
14. 不新增通用多后端 debugger 平台。
15. 不把 stale/missing artifact 当 current evidence。
16. 不伪造窗口句柄、breakpoint hits、post_entry_events、branch_eip、eflags、instruction、condition、next_eip。
17. 不读取完整 solve_reports/。
18. 不读取完整 PROJECT_PROGRESS_LOG.txt。
19. 不修改 .codex-skills/。
20. 不修改 sample_corpus/reverse/。
21. 不修改 reverse_agent/harness.py。
22. 不修改 reverse_agent/sample_solver.py。
23. 不提交完整 solve_reports/。
24. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 Frida breakpoint-only bounded control-flow surface。
3. 只允许诊断当前 window discovery path，不允许扩展到通用 UI 自动化平台。
4. 允许在 sidecar 内写 window discovery sub-stage checkpoint 与 flush-safe partial artifact。
5. 允许 wrapper 捕获 TimeoutExpired 并解析已有 per-candidate partial artifact/log。
6. 允许最多两个 bounded window discovery 方法：现有 app.top_window 路线 + 一个明确记录的 inventory fallback。
7. 不允许扩大默认 per_probe_timeout；测试里的更小 timeout 只能用于 mock 或 bounded diagnostic。
8. 不允许 dump 任意大内存，不允许保存 material bytes，不允许输出 candidate score/ranking。
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
project_state.artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.current_bottleneck
project_state/rounds/round_20260601_ui_trigger_lifecycle_diagnostics/round_manifest.json
```

允许有界读取 current upstream artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_narrower_post_entry_breakpoint_audit/compare_handoff_narrower_post_entry_breakpoint_audit.json
```

允许检查和修改：

```text
reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py
reverse_agent/strategies/compare_aware_search.py
reverse_agent/project_state.py
tests/test_compare_aware_search_strategy.py
tests/test_project_state.py
project_state/artifact_index.json
project_state/current_state.json
project_state/codex_execution_report.md
project_state/pytest_result.txt
```

不允许修改：

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
6. compare_handoff_narrower_post_entry_breakpoint_audit freshness 是否为 current。
7. 是否保持同 3 个固定候选。
8. 是否没有新增候选、扩大 beam/topN/budget/timeout/frontier_limit。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/、sample_corpus/reverse/、harness.py、sample_solver.py。
13. 是否给每个候选写出 window discovery sub-stage lifecycle checkpoint。
14. 是否能区分 process alive / app connected / top_window attempted / top_window returned / inventory fallback / visible window count。
15. 是否记录 per-candidate window_discovery_diagnostics，包括 pid_alive、top_window_attempted、top_window_returned、top_window_error、window_inventory_count、visible_window_count、candidate_windows。
16. 是否保留上一轮 Frida lifecycle evidence，不回退到 spawn/attach/script/breakpoint blocker。
17. 是否把 window_discovery_timeout 细化为更具体 blocker；如果没有，是否明确 window discovery instrumentation gap。
18. 是否没有伪造窗口句柄、breakpoint hits、post-entry events、branch EIP、EFLAGS、condition、next-EIP。
19. 是否明确 breakpoint_probe_allowed=false。
20. artifact_index 是否 additive 更新，不删除旧字段。
21. current_state 是否只更新当前 bottleneck/latest artifact 摘要，不写入 skill。
22. negative_results 是否未被重复违反。
23. lint-decision 是否通过；若执行后 state rebuild 导致 digest mismatch，必须标记 PARTIAL/NEEDS_REVIEW，不得写 SUCCESS/ACCEPTED。
24. lint-report 是否通过。
25. 相关 pytest 是否通过。
26. git diff --check 是否通过。
27. pytest_result.txt 是否与真实命令结果一致。
28. codex_report_summary 是否与当前 decision_id 匹配。
29. 是否归档本轮 round，或明确说明未归档原因。
```

## 6. Implementation Scope

### 6.1 Window discovery sub-stage checkpoints

增强：

```text
reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py
```

必须让 sidecar 在 window discovery 阶段写出 flush-safe partial artifact 或 log checkpoint：

```text
1. window_discovery_started
2. process_liveness_checked
3. app_connection_rechecked
4. top_window_attempted
5. top_window_returned / top_window_failed / top_window_timeout
6. window_inventory_attempted
7. window_inventory_captured / window_inventory_failed / window_inventory_timeout
8. visible_window_filter_applied
9. primary_window_selected / primary_window_unavailable
10. window_discovery_finished
```

如果 subprocess 被 wrapper timeout 杀死，已有 partial artifact 必须仍能说明最后确认 window sub-stage。

### 6.2 Bounded window inventory fallback

允许最小范围内改造 window discovery，但必须保持 bounded：

```text
1. 优先保留当前 app.top_window() 路线并记录 method=app.top_window。
2. 若 app.top_window() 没有返回或 timeout，允许新增一个明确记录的 fallback inventory method。
3. fallback 只能枚举当前 pid 关联窗口，不能扫描全系统窗口作为通用平台。
4. 每个 method 必须记录 attempted、returned、error、duration_ms、timeout_stage。
5. candidate_windows 最多保留前 10 个摘要字段：title、class_name、handle、visible、enabled、rectangle。
6. 不允许通过增加全局 timeout 掩盖卡点。
7. 若 window discovery 成功但 input lookup 失败，classification 必须推进到 input_control_lookup_failed / input_control_lookup_timeout，而不是停在 window_discovery。
```

### 6.3 Wrapper timeout handling

增强 `CompareAwareSearchStrategy` 中 current narrower audit runner 的 timeout fallback。

最小要求：

```text
1. 捕获 TimeoutExpired 后读取 candidate partial artifact 和 sidecar log。
2. 不直接把 timeout 继续归为 window_discovery_timeout。
3. 根据 window_discovery_diagnostics.last_window_stage 细化 classification。
4. 写入 candidate_invocation_health，不删除已有 lifecycle_diagnostics / ui_trigger_diagnostics。
5. 如果 partial artifact 不存在，classification 才能是 window_discovery_instrumentation_gap，并标明 wrapper/sidecar gap。
```

### 6.4 Artifact schema additions

在现有 artifact 上 additive 增加字段，不删除旧字段：

```json
{
  "window_discovery_schema_version": 1,
  "window_discovery_diagnostics": {
    "classification": "...",
    "last_window_stage": "...",
    "timeout_stage": "...",
    "process_liveness": {},
    "top_window": {},
    "window_inventory": {},
    "selected_window": {}
  },
  "candidates": [
    {
      "candidate_hex": "...",
      "window_discovery": {
        "last_window_stage": "...",
        "process_alive": true,
        "top_window": {
          "attempted": true,
          "returned": false,
          "duration_ms": 0,
          "error": ""
        },
        "window_inventory": {
          "attempted": true,
          "returned": false,
          "window_count": 0,
          "visible_window_count": 0,
          "candidate_windows": []
        },
        "selected_window": {
          "available": false,
          "title": "",
          "class_name": "",
          "handle": ""
        }
      },
      "classification": "..."
    }
  ]
}
```

仍必须保留：

```text
lifecycle_schema_version
lifecycle_diagnostics
ui_trigger_schema_version
ui_trigger_diagnostics
candidate_invocation_health
candidate_generation_changed=false
ranking_changed=false
search_budget_changed=false
beam_budget_topn_timeout_frontier_limit_expanded=false
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

### 6.5 Project state projection

`project_state.py` 必须继续 additive 投影：

```text
artifact_index.latest_artifacts.compare_handoff_narrower_post_entry_breakpoint_audit
artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.stage=compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.reason=<specific window discovery classification>
```

如果 classification 仍是 `window_discovery_timeout`，必须附加：

```text
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.window_discovery_diagnostics.classification
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.window_discovery_diagnostics.last_window_stage
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.window_discovery_diagnostics.timeout_stage
```

不得删除旧 `lifecycle_diagnostics`、`ui_trigger_diagnostics`、`compare_handoff_post_entry_step_runtime_audit` 或其他 artifact fields。不得把动态事实写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_narrower_post_entry_breakpoint_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "window_discovery or ui_trigger or narrower_post_entry or lifecycle"
python -m pytest -q tests\test_project_state.py -k "window_discovery or ui_trigger or narrower_post_entry or lifecycle or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果本地 runtime 可执行，必须额外运行一次 bounded artifact generation，但仍保持 3 个固定候选和现有 timeout，不做扩时实验：

```text
python -c "from pathlib import Path; from reverse_agent.strategies.compare_aware_search import run_compare_handoff_narrower_post_entry_breakpoint_audit; target=Path(r'F:\reverse-agent\solve_reports\samplereverse_patched.exe'); artifacts_dir=Path(r'solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit'); result=run_compare_handoff_narrower_post_entry_breakpoint_audit(target=target, artifacts_dir=artifacts_dir, per_probe_timeout=2.2, source_payload={'source_run':'sr_arg0_hook_readiness_ordering_20260526_r1','classification':'window_discovery_timeout'}, run_name='sr_arg0_hook_readiness_ordering_20260526_r1'); print(result['result_path']); print(result['payload'].get('classification')); print(result['payload'].get('window_discovery_diagnostics', {}))"
```

如果 runtime 环境仍不能执行，必须：

```text
1. 生成 blocked/partial artifact。
2. 写明更具体 window discovery blocker 或明确 wrapper/sidecar window discovery instrumentation gap。
3. 不伪造窗口句柄、breakpoint hits 或 post_entry_events。
4. 不把 runtime_sidecar_executed 写成 true，除非确实进入 sidecar lifecycle 并有 checkpoint 证据。
5. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_window_discovery_lifecycle_diagnostics
round_id=round_20260601_window_discovery_lifecycle_diagnostics
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. artifact_index.latest_artifacts_v2 中 compare_handoff_narrower_post_entry_breakpoint_audit 不是 current。
2. 3 个固定候选无法全部保留。
3. 需要新增候选、扩大 beam/topN/budget/timeout/frontier_limit 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
5. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
7. Frida lifecycle 又退回 spawn/attach/script load/breakpoint install blocker；输出 regression_to_pre_ui_lifecycle 并停止。
8. UI trigger lifecycle 退回 button/input 阶段以前但没有 window evidence；输出 window_discovery_instrumentation_gap 并停止。
9. sidecar 无法写出任何 window discovery sub-stage checkpoint；输出 window_discovery_instrumentation_gap 并停止。
10. 进程在 window discovery 前退出；输出 process_exited_before_window_discovery 并停止。
11. top_window 卡死或失败；输出 top_window_call_timeout / top_window_call_failed，并结合 inventory fallback 结果停止或继续。
12. window inventory 为空；输出 process_window_inventory_empty 或 process_no_visible_window 并停止。
13. window discovery 成功但 input Edit 控件无法定位；输出 input_control_lookup_failed / input_control_lookup_timeout 并停止。
14. input/button 后续阶段触发新的更具体 blocker；输出相应 blocker 并停止。
15. button action 返回但 0x2338/0x1b50 不命中；输出 button_action_returned_no_entry_hit 或 entry_breakpoint_not_hit_after_ui_trigger 并停止。
16. handoff_helper_entry 命中但 successor surface 不命中；输出 successor_breakpoint_not_hit_after_ui_trigger 并停止。
17. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_ui_trigger_lifecycle_diagnostics",
  "round_id": "round_20260601_ui_trigger_lifecycle_diagnostics",
  "based_on_state_build_id": "state_20260601_145342_027e5d2b1c2e",
  "based_on_state_digest": "027e5d2b1c2e18cae790013dae0137dd2c2ddd73b3f5b32976e8100ae23ec03a",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但只处理上一轮已经细化出的 runtime blocker：

```text
compare_handoff_narrower_post_entry_breakpoint_audit / ui_trigger_timeout
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

本轮目标不是求最终 flag，也不是继续候选搜索；目标是把上一轮的：

```text
ui_trigger_timeout
```

继续拆成可审计、可复现、可下一步行动的最小 UI trigger lifecycle blocker。

必须增强当前 artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit.json
```

本轮必须回答：

```text
1. ui_trigger_timeout 到底发生在 window discovery、input edit lookup、input text set、button lookup、button invoke/click、post-trigger wait，还是 breakpoint observation 阶段。
2. 既然上一轮已确认 dependency_import_ok、frida.spawn、frida.attach、script load、breakpoint install、frida.resume、ui_connect 都 OK，本轮不得回退到 spawn/attach 诊断。
3. 每个固定候选必须记录 bounded UI control diagnostics：window title/class/handle 可用性、目标 Edit/Button 控件是否找到、是否 enabled/visible、输入写入是否成功、按钮触发方法是否返回。
4. 如果按钮触发方法卡死，必须区分 invoke_timeout、click_input_timeout、set_focus_timeout、button_action_timeout，而不是继续笼统写 ui_trigger_timeout。
5. 如果按钮触发返回但没有 breakpoint hit，必须区分 post_trigger_no_entry_hit、entry_breakpoint_not_hit 或 observation_wait_timeout。
6. 不得把本轮变成 GUI 自动化平台建设、通用 pywinauto 兼容层、Base64/RC4 probe、material capture、候选搜索或 timeout 扩大实验。
```

本轮的验收标准是 **UI trigger blocker specificity improves**。即使目标仍不能进入 decrypt path，也必须从 `ui_trigger_timeout` 细化为以下之一：

```text
window_discovery_failed
window_discovery_timeout
input_control_lookup_failed
input_control_lookup_timeout
input_set_text_failed
input_set_text_timeout
input_value_not_confirmed
button_control_lookup_failed
button_control_lookup_timeout
button_disabled_or_invisible
button_invoke_failed
button_invoke_timeout
button_click_failed
button_click_timeout
button_action_returned_no_entry_hit
post_trigger_observation_timeout
entry_breakpoint_not_hit_after_ui_trigger
successor_breakpoint_not_hit_after_ui_trigger
post_entry_breakpoint_observed_after_ui_trigger
ui_trigger_instrumentation_gap
```

如果无法进一步细化，Codex 必须明确说明是 wrapper/sidecar UI instrumentation gap，并给出缺失的最小证据；不得声称成功。

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
state_build_id=state_20260601_145342_027e5d2b1c2e
state_digest=027e5d2b1c2e18cae790013dae0137dd2c2ddd73b3f5b32976e8100ae23ec03a
source_git_commit=48d4efbca602
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
report_id=report_20260601_frida_spawn_attach_lifecycle_diagnostics
based_on_decision_id=decision_20260601_frida_spawn_attach_lifecycle_diagnostics
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
```

当前 bottleneck：

```text
stage=compare_handoff_narrower_post_entry_breakpoint_audit
reason=ui_trigger_timeout
confidence=medium
```

current artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit\compare_handoff_narrower_post_entry_breakpoint_audit.json
  sha256=2e06f2e5db861b150a16cf21963a40941efa2acf032f1e8ae5851fe200fd9e7c
  size_bytes=30776
```

上一轮 artifact 摘要：

```text
classification=ui_trigger_timeout
candidate_count=3
target_launch_ok_count=3
breakpoint_install_ok_count=12
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

上一轮 lifecycle 已确认阶段：

```text
dependency_import_ok
frida_spawn_ok
frida_attach_ok
script_load_ok
breakpoint_install_ok
frida_resume_ok
ui_connect_ok
last_confirmed_stage=ui_trigger_attempted
timeout_stage=ui_trigger
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
2. compare_handoff_post_entry_step_runtime_audit 是 current，但只作为上一轮 step_api_unavailable 背景。
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
9. 不把 UI trigger diagnostics 变成 material probe。
10. 不继续只输出 ui_trigger_timeout 而不写 UI sub-stage checkpoint。
11. 不把 button trigger timeout 当作 decrypt path 失败的充分证据；必须写出最后确认阶段。
12. 不建设通用 GUI automation framework / pywinauto adapter 平台。
13. 不默认增加 timeout 来掩盖 UI lifecycle 缺证。
14. 不新增通用多后端 debugger 平台。
15. 不把 stale/missing artifact 当 current evidence。
16. 不伪造 breakpoint hits、post_entry_events、branch_eip、eflags、instruction、condition、next_eip。
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
3. 只允许诊断当前 UI trigger path，不允许扩展到通用 UI 自动化平台。
4. 允许在 sidecar 内写 UI sub-stage checkpoint 与 flush-safe partial artifact。
5. 允许 wrapper 捕获 TimeoutExpired 并解析已有 per-candidate partial artifact/log。
6. 允许最多两个 bounded trigger methods：现有 trigger method + 一个明确记录的 fallback method。
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
project_state/rounds/round_20260601_frida_spawn_attach_lifecycle_diagnostics/round_manifest.json
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
13. 是否给每个候选写出 UI sub-stage lifecycle checkpoint。
14. 是否能区分 window discovery / input lookup / input set / button lookup / button action / post-trigger observation。
15. 是否记录 per-candidate ui_trigger_diagnostics，包括 window metadata、control lookup results、input set result、trigger method attempted、trigger method returned/timeout/error、post-trigger observation status。
16. 是否保留上一轮 Frida lifecycle evidence，不回退到 spawn/attach blocker。
17. 是否把 ui_trigger_timeout 细化为更具体 blocker；如果没有，是否明确 UI instrumentation gap。
18. 是否没有伪造 breakpoint hits、post-entry events、branch EIP、EFLAGS、condition、next-EIP。
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

### 6.1 UI trigger sub-stage checkpoints

增强：

```text
reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py
```

必须让 sidecar 在 UI trigger 阶段写出 flush-safe partial artifact 或 log checkpoint：

```text
1. ui_window_discovery_attempted
2. ui_window_discovery_ok / ui_window_discovery_failed
3. ui_control_inventory_captured
4. ui_input_lookup_attempted
5. ui_input_lookup_ok / ui_input_lookup_failed
6. ui_input_set_text_attempted
7. ui_input_set_text_ok / ui_input_set_text_failed
8. ui_input_value_confirm_attempted
9. ui_input_value_confirm_ok / ui_input_value_confirm_failed
10. ui_button_lookup_attempted
11. ui_button_lookup_ok / ui_button_lookup_failed
12. ui_button_state_checked
13. ui_button_trigger_method_selected
14. ui_button_invoke_attempted
15. ui_button_invoke_returned / ui_button_invoke_failed / ui_button_invoke_timeout
16. ui_button_click_attempted
17. ui_button_click_returned / ui_button_click_failed / ui_button_click_timeout
18. ui_trigger_returned
19. post_trigger_observation_wait_started
20. entry_breakpoint_hit_after_ui_trigger / post_trigger_observation_timeout
21. final_artifact_write_attempted
22. final_artifact_write_ok / final_artifact_write_failed
```

如果 subprocess 被 wrapper timeout 杀死，已有 partial artifact 必须仍能说明最后确认 UI sub-stage。

### 6.2 Bounded trigger method handling

允许最小范围内改造 `_trigger_decrypt` 或其调用方式，但必须保持 bounded：

```text
1. 优先保留当前触发方法并记录 method name。
2. 若当前方法卡在 button action，可新增一个明确记录的 fallback method，例如 invoke vs click_input 二选一。
3. 最多两个 trigger methods，不允许做无限 fallback 或枚举所有 UIA pattern。
4. 每个 method 必须记录 attempted、returned、error、duration_ms、timeout_stage。
5. 不允许通过增加全局 timeout 掩盖卡点。
6. 若 button action 返回但没有 breakpoint hit，classification 必须从 action timeout 转为 post_trigger_observation_timeout 或 entry_breakpoint_not_hit_after_ui_trigger。
```

### 6.3 Wrapper timeout handling

增强 `CompareAwareSearchStrategy` 中 current narrower audit runner 的 timeout fallback。

最小要求：

```text
1. 捕获 TimeoutExpired 后读取 candidate partial artifact 和 sidecar log。
2. 不直接把 timeout 继续归为 ui_trigger_timeout。
3. 根据 ui_trigger_diagnostics.last_ui_stage 细化 classification。
4. 写入 candidate_invocation_health，不删除已有 lifecycle_diagnostics。
5. 如果 partial artifact 不存在，classification 才能是 ui_trigger_instrumentation_gap，并标明 wrapper/sidecar gap。
```

### 6.4 Artifact schema additions

在现有 artifact 上 additive 增加字段，不删除旧字段：

```json
{
  "ui_trigger_schema_version": 1,
  "ui_trigger_diagnostics": {
    "classification": "...",
    "last_ui_stage": "...",
    "timeout_stage": "...",
    "method_counts": {},
    "control_lookup_counts": {},
    "post_trigger_observation": {}
  },
  "candidates": [
    {
      "candidate_hex": "...",
      "ui_trigger": {
        "last_ui_stage": "...",
        "window": {
          "discovered": true,
          "title": "",
          "class_name": "",
          "handle": ""
        },
        "input_control": {
          "lookup_attempted": true,
          "lookup_ok": true,
          "set_text_attempted": true,
          "set_text_ok": true,
          "value_confirmed": true
        },
        "button_control": {
          "lookup_attempted": true,
          "lookup_ok": true,
          "enabled": true,
          "visible": true
        },
        "trigger_methods": [
          {
            "method": "invoke_or_click",
            "attempted": true,
            "returned": false,
            "duration_ms": 0,
            "error": ""
          }
        ],
        "post_trigger_observation": {
          "entry_breakpoint_hit": false,
          "successor_breakpoint_hit": false,
          "observed_events": []
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
current_state.current_bottleneck.reason=<specific UI trigger classification>
```

如果 classification 仍是 `ui_trigger_timeout`，必须附加：

```text
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.ui_trigger_diagnostics.classification
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.ui_trigger_diagnostics.last_ui_stage
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.ui_trigger_diagnostics.timeout_stage
```

不得删除旧 `lifecycle_diagnostics`、`compare_handoff_post_entry_step_runtime_audit` 或其他 artifact fields。不得把动态事实写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_narrower_post_entry_breakpoint_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "ui_trigger or narrower_post_entry or lifecycle"
python -m pytest -q tests\test_project_state.py -k "ui_trigger or narrower_post_entry or lifecycle or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果本地 runtime 可执行，必须额外运行一次 bounded artifact generation，但仍保持 3 个固定候选和现有 timeout，不做扩时实验：

```text
python -c "from pathlib import Path; from reverse_agent.strategies.compare_aware_search import run_compare_handoff_narrower_post_entry_breakpoint_audit; target=Path(r'F:\reverse-agent\solve_reports\samplereverse_patched.exe'); artifacts_dir=Path(r'solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit'); result=run_compare_handoff_narrower_post_entry_breakpoint_audit(target=target, artifacts_dir=artifacts_dir, per_probe_timeout=2.2, source_payload={'source_run':'sr_arg0_hook_readiness_ordering_20260526_r1','classification':'ui_trigger_timeout'}, run_name='sr_arg0_hook_readiness_ordering_20260526_r1'); print(result['result_path']); print(result['payload'].get('classification')); print(result['payload'].get('ui_trigger_diagnostics', {}))"
```

如果 runtime 环境仍不能执行，必须：

```text
1. 生成 blocked/partial artifact。
2. 写明更具体 UI blocker 或明确 wrapper/sidecar UI instrumentation gap。
3. 不伪造 breakpoint hits 或 post_entry_events。
4. 不把 runtime_sidecar_executed 写成 true，除非确实进入 sidecar lifecycle 并有 checkpoint 证据。
5. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_ui_trigger_lifecycle_diagnostics
round_id=round_20260601_ui_trigger_lifecycle_diagnostics
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
8. sidecar 无法写出任何 UI sub-stage checkpoint；输出 ui_trigger_instrumentation_gap 并停止。
9. window 无法发现；输出 window_discovery_failed / window_discovery_timeout 并停止。
10. input Edit 控件无法定位或无法写入；输出 input_control_lookup_failed / input_set_text_failed / input_set_text_timeout 并停止。
11. Button 控件无法定位、不可见或不可用；输出 button_control_lookup_failed / button_disabled_or_invisible 并停止。
12. button action 阶段卡住；输出 button_invoke_timeout / button_click_timeout / button_action_timeout 并停止。
13. button action 返回但 0x2338/0x1b50 不命中；输出 button_action_returned_no_entry_hit 或 entry_breakpoint_not_hit_after_ui_trigger 并停止。
14. handoff_helper_entry 命中但 successor surface 不命中；输出 successor_breakpoint_not_hit_after_ui_trigger 并停止。
15. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

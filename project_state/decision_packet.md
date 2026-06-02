```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260602_window_discovery_api_blocker_audit",
  "round_id": "round_20260602_window_discovery_api_blocker_audit",
  "based_on_state_build_id": "state_20260601_154138_7dbbabc8dcd6",
  "based_on_state_digest": "7dbbabc8dcd65e5cbd8445677c91db8f8d493602afe1be5031a485da11a640f0",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但只处理当前已收窄出的窗口发现 API blocker：

```text
compare_handoff_narrower_post_entry_breakpoint_audit / window_discovery_api_blocked
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

本轮目标不是求最终 flag，不是候选搜索，也不是继续扩大 GUI 自动化能力；目标是对 `window_discovery_api_blocked` 做一个更小范围的原因归因审计。

必须回答：

```text
1. 当前 blocker 是 pywinauto backend/API 选择问题、窗口生命周期问题、进程/窗口句柄不可枚举问题，还是 sidecar instrumentation gap。
2. 为什么上一轮 pid_alive=true，但 app.top_window 和 pid-scoped app.windows inventory fallback 均没有返回窗口。
3. 是否存在可审计的非 material、非 crypto、非 candidate-ranking 的窗口枚举证据，可把 blocker 细化到一个明确原因。
4. 如果无法定位具体原因，必须输出最小缺失证据，而不是继续笼统报告 window_discovery_api_blocked。
```

本轮验收标准是把当前 blocker 细化为以下之一：

```text
window_backend_mismatch
window_lifecycle_no_window_created
window_lifecycle_window_created_too_late
window_exists_but_not_visible
window_exists_but_not_accessible_by_backend
pid_alive_but_no_owned_window
win32_enum_windows_succeeded_pywinauto_failed
win32_enum_windows_empty
uia_backend_succeeded_win32_failed
window_discovery_instrumentation_gap
window_discovery_succeeded_input_lookup_next
```

如果窗口发现成功，只允许进入已有 input/button lookup 的下一步诊断；不得升级为 material capture、crypto hook、candidate ranking 或通用 GUI automation framework。

## 2. Current Evidence

当前主线：

```text
reverse_solving
```

当前样本：

```text
samplereverse
```

当前 state：

```text
state_build_id=state_20260601_154138_7dbbabc8dcd6
state_digest=7dbbabc8dcd65e5cbd8445677c91db8f8d493602afe1be5031a485da11a640f0
source_git_commit=ad828fe1f69b
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
workflow_status=REPORT_AVAILABLE
review_status=PENDING_REVIEW
```

当前 skill profiles：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

`.codex-skills/registry.json` 当前只登记两个 active skill：

```text
reverse-agent-iteration@v2
samplereverse-frontier@v2
```

当前 `task_packet.task` / `derived_task`：

```text
Review bounded window discovery diagnostics
```

它只是状态派生建议；本 decision 才是当前轮执行权威。

上一轮 Codex report：

```text
report_id=report_20260601_window_discovery_lifecycle_diagnostics
based_on_decision_id=decision_20260601_window_discovery_lifecycle_diagnostics
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
```

上一轮测试和状态：

```text
focused pytest passed: 3 passed / 11 passed
project_state build passed
lint-report OK
lint-decision failed as expected because state digest changed after rebuild
current bottleneck=compare_handoff_narrower_post_entry_breakpoint_audit/window_discovery_api_blocked
```

当前直接 artifact：

```text
kind=compare_handoff_narrower_post_entry_breakpoint_audit
freshness=current
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit\compare_handoff_narrower_post_entry_breakpoint_audit.json
sha256=070e7b8eb7d3b671b172894c511f57e365c7bffbb95f09420c4914ac1977c7f1
size_bytes=183016
```

上一轮窗口发现证据：

```text
classification=window_discovery_api_blocked
candidate_count=3
pid_alive=true for all 3 candidates
app.top_window attempted for all 3 candidates, returned for 0
pid-scoped app.windows inventory fallback attempted for all 3 candidates, returned for 0
selected_window_available=false
candidate_windows=[]
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

固定候选必须保持不变：

```text
78d540b49c59077041414141414141
5a3e7f46ddd474d041414141414141
78d540b49c59076f41414141414141
```

artifact freshness 判断：

```text
1. compare_handoff_narrower_post_entry_breakpoint_audit 是 current，是本轮 blocker 的直接来源。
2. compare_handoff_post_entry_step_runtime_audit、compare_handoff_branch_operand_runtime_audit、compare_handoff_hook_surface_repair_audit 等同 run artifacts 可作为 current 背景，但不得替代本轮窗口发现证据。
3. base64_rc4_static_point_discovery、function_semantic_audit、compare_handoff_return_site_probe 等 legacy artifacts 只能作为 stale/background，不得作为新的 current runtime 证据。
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
10. 不默认增加 timeout 来掩盖 window discovery 缺证。
11. 不建设通用 GUI automation framework / pywinauto adapter 平台。
12. 不新增通用多后端 debugger 平台。
13. 不把 stale/missing artifact 当 current evidence。
14. 不伪造窗口句柄、breakpoint hits、post_entry_events、branch_eip、eflags、instruction、condition、next_eip。
15. 不读取完整 solve_reports/。
16. 不读取完整 PROJECT_PROGRESS_LOG.txt。
17. 不修改 .codex-skills/。
18. 不修改 sample_corpus/reverse/。
19. 不修改 reverse_agent/harness.py。
20. 不修改 reverse_agent/sample_solver.py。
21. 不提交完整 solve_reports/。
22. 不把 task_packet.task / derived_task 当成当前轮执行权威。
23. 不重复 negative_results 中已禁止方向。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许诊断当前 window discovery path。
3. 允许在 sidecar 内加入 bounded Win32/UIA/window-owner 枚举检查，但必须只记录窗口元数据：pid、handle、title、class、visible/enabled、backend、owned_by_pid。
4. 允许比较 pywinauto win32 backend、pywinauto uia backend、直接 EnumWindows/EnumChildWindows 的差异。
5. 允许 wrapper 捕获 TimeoutExpired 并解析已有 per-candidate partial artifact/log。
6. 不允许扩大默认 per_probe_timeout；测试中的小 timeout 只能用于 mock 或 bounded diagnostic。
7. 不允许 dump 任意大内存，不允许保存 material bytes，不允许输出 candidate score/ranking。
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

必须验证：

```text
.codex-skills/registry.json
project_state.artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.current_bottleneck
```

允许有界读取 current upstream artifact，但不得遍历完整 solve_reports：

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
13. 是否对 pywinauto win32 backend、pywinauto uia backend、直接 EnumWindows/EnumChildWindows 的差异作出 bounded 判断。
14. 每个候选是否记录 pid_alive、process_exit_code、backend attempted/returned/failed、window_count、visible_window_count、owned_window_count。
15. 如果窗口枚举成功，是否只记录窗口元数据，未记录 material bytes 或 crypto buffer。
16. 是否把 final classification 从 window_discovery_api_blocked 细化为验收列表之一。
17. 若无法细化，是否明确输出 window_discovery_instrumentation_gap 及最小缺失证据。
18. 是否没有伪造 window handles、breakpoint hits、post-entry events、branch EIP/EFLAGS/condition/next-EIP。
19. artifact_index update 是否 additive，且 latest_artifacts_v2 freshness/provenance 正确。
20. current_state 是否反映新的 blocker classification。
21. codex_report_summary 是否存在，based_on_decision_id 是否匹配 decision_20260602_window_discovery_api_blocker_audit。
22. pytest_result.txt 是否记录真实测试命令和结果。
```

## 6. Implementation Scope

建议实现范围：

```text
1. 在 compare_handoff_narrower_post_entry_breakpoint_audit.py 中增加 bounded window API attribution block。
2. 对每个固定候选记录：
   - process_pid
   - pid_alive_before_window_checks
   - process_exit_code_if_available
   - pywinauto_win32_top_window_attempted/returned/failed
   - pywinauto_win32_windows_attempted/returned/failed
   - pywinauto_uia_top_window_attempted/returned/failed
   - pywinauto_uia_windows_attempted/returned/failed
   - direct_enum_windows_attempted/returned/failed
   - direct_enum_windows_count
   - direct_enum_visible_count
   - direct_enum_owned_by_pid_count
   - selected_window_backend
   - selected_window_metadata
   - final_window_discovery_reason
3. 在 CompareAwareSearchStrategy 中保留 per-candidate partial artifacts，并聚合 window API attribution diagnostics。
4. 在 project_state.py 中把新的 window API attribution summary 投影到 current_state。
5. 测试只覆盖分类、聚合、project_state 投影和 TimeoutExpired partial artifact 读取，不要求真实 GUI 环境。
```

分类规则建议：

```text
1. direct EnumWindows 能找到 pid-owned visible window，但 pywinauto win32/uia 均失败 -> win32_enum_windows_succeeded_pywinauto_failed。
2. uia backend 成功、win32 backend 失败 -> uia_backend_succeeded_win32_failed 或 window_backend_mismatch。
3. win32 backend 成功、uia backend 失败 -> window_backend_mismatch，但可继续现有 input/button lookup。
4. direct EnumWindows 返回 0 个 pid-owned window，且 process 仍 alive -> pid_alive_but_no_owned_window 或 win32_enum_windows_empty。
5. 只找到不可见窗口 -> window_exists_but_not_visible。
6. 多次 lifecycle checkpoint 显示窗口在较晚阶段出现 -> window_lifecycle_window_created_too_late。
7. 所有 API 均因 wrapper/timeout/exception 无法产生可信元数据 -> window_discovery_instrumentation_gap。
```

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_narrower_post_entry_breakpoint_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "window_discovery or window_api or narrower_post_entry or lifecycle"
python -m pytest -q tests\test_project_state.py -k "window_discovery or window_api or artifact_index or current_bottleneck"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
git diff --check
```

允许运行一个 bounded runtime artifact generation command，但必须满足：

```text
1. 固定 3 个候选。
2. 不运行 Base64/RC4 breakpoint probe。
3. 不做 material capture。
4. 不保存 crypto/material bytes。
5. 不扩大 candidate/frontier/budget/timeout。
6. 输出 artifact classification 必须是验收列表之一。
```

如果 `lint-decision` 因 build 后 state digest 变化失败，Codex 必须在报告中明确说明，并把 report status 设为 `PARTIAL` 或 `NEEDS_REVIEW`，不得标记为 `SUCCESS/ACCEPTED`。

## 8. Stop Conditions

立即停止并写报告：

```text
1. 已把 window_discovery_api_blocked 细化为验收列表之一。
2. 发现窗口枚举成功并可进入已有 input/button lookup，但不得继续到 material/candidate work。
3. 发现直接 EnumWindows 与 pywinauto backend 结果冲突。
4. 三种 bounded window discovery 方法均无法产生可信元数据，分类为 window_discovery_instrumentation_gap。
5. 任何测试失败、lint-report 失败、codex_report_summary 缺失、based_on_decision_id mismatch。
6. 需要修改 .codex-skills/、harness.py、sample_solver.py 或读取完整 solve_reports/ 才能继续。
7. 任何步骤诱导 Base64/RC4 breakpoint probe、material capture、crypto hook、候选扩展或 budget/timeout 扩张。
```

本轮完成后，必须更新：

```text
project_state/codex_execution_report.md
project_state/pytest_result.txt
project_state/current_state.json
project_state/artifact_index.json
```

报告顶部必须包含 `codex_report_summary`，并且：

```text
based_on_decision_id=decision_20260602_window_discovery_api_blocker_audit
round_id=round_20260602_window_discovery_api_blocker_audit
```
```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_frida_spawn_attach_lifecycle_diagnostics",
  "round_id": "round_20260601_frida_spawn_attach_lifecycle_diagnostics",
  "based_on_state_build_id": "state_20260601_104951_ecca8f86272a",
  "based_on_state_digest": "ecca8f86272aa5a550e93ce3f4b554ba233a8584ab64e21073f80526d6ae3b9e",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但只处理上一轮新暴露的 runtime blocker：

```text
compare_handoff_narrower_post_entry_breakpoint_audit / frida_attach_or_spawn_failed
```

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

本轮目标不是求最终 flag，也不是继续候选搜索；目标是把上一轮笼统的：

```text
frida_attach_or_spawn_failed
```

拆成可审计、可复现、可下一步行动的最小 runtime lifecycle blocker。

必须增强或补充当前 artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit.json
```

本轮必须回答：

```text
1. sidecar timeout 到底发生在 subprocess 启动前、Frida import、frida.spawn、frida.attach、script.create/load、breakpoint install、frida.resume、pywinauto connect、UI trigger，还是 artifact write 阶段。
2. 每个固定候选是否写出了 per-candidate lifecycle checkpoint，即使 subprocess timeout 也不能只留下“sidecar timed out before writing candidate artifact”。
3. 如果仍然 timeout，必须记录最后已确认阶段、stdout/stderr tail、candidate log path、candidate artifact path、returncode/timeout flag。
4. 如果 spawn/attach 成功但 breakpoint install 失败，必须区分 breakpoint_install_failed，而不是继续归为 frida_attach_or_spawn_failed。
5. 如果 breakpoint 安装成功但未命中，必须区分 entry_breakpoint_not_hit 或 successor_breakpoint_not_hit。
6. 不得把本轮变成 Base64/RC4 probe、material capture、候选搜索、timeout 扩大实验或通用 debugger 平台建设。
```

本轮的验收标准是 **blocker specificity improves**。即使仍无法运行目标进程，也必须从 `frida_attach_or_spawn_failed` 细化为以下之一：

```text
debugger_dependency_missing
target_missing_or_unlaunchable
frida_spawn_failed
frida_spawn_timeout
frida_attach_failed
frida_attach_timeout
script_create_or_load_failed
script_load_timeout
breakpoint_install_failed
breakpoint_install_timeout
frida_resume_failed
ui_connect_failed
ui_connect_timeout
ui_trigger_failed
ui_trigger_timeout
entry_breakpoint_not_hit
successor_breakpoint_not_hit
post_entry_breakpoint_observed
candidate_artifact_write_failed
subprocess_timeout_after_lifecycle_checkpoint
```

如果无法进一步细化，Codex 必须明确说明是 wrapper/sidecar instrumentation gap，并给出缺失的最小证据；不得声称成功。

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
state_build_id=state_20260601_104951_ecca8f86272a
state_digest=ecca8f86272aa5a550e93ce3f4b554ba233a8584ab64e21073f80526d6ae3b9e
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
workflow_status=REPORT_AVAILABLE
review_status=PENDING_REVIEW
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Review bounded narrower post-entry breakpoint blocker
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

上一轮 Codex report：

```text
report_id=report_20260601_narrower_post_entry_breakpoint_audit
based_on_decision_id=decision_20260601_narrower_post_entry_breakpoint_audit
status=PARTIAL
acceptance_recommendation=NEEDS_REVIEW
```

当前 bottleneck：

```text
stage=compare_handoff_narrower_post_entry_breakpoint_audit
reason=frida_attach_or_spawn_failed
confidence=medium
```

current artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit\compare_handoff_narrower_post_entry_breakpoint_audit.json
  sha256=096319424f3fbd623c07a1ff5185ea98e5cc9c506ce852086ac088940324de25
```

上一轮 artifact 摘要：

```text
classification=frida_attach_or_spawn_failed
overall_classification=frida_attach_or_spawn_failed
candidate_count=3
target_launch_attempted_count=3
target_launch_ok_count=0
breakpoint_install_attempted_count=0
breakpoint_install_ok_count=0
breakpoint_hit_counts={}
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

上一轮 per-candidate 共同问题：

```text
target_launch.attempted=true
target_launch.ok=false
target_launch.error="sidecar timed out before writing candidate artifact; returncode=124"
event_sequence=[]
handoff_helper_entry_observed=false
successor_surface_observed=false
breakpoints install_attempted=false/install_ok=false/hit=false
breakpoint error="sidecar timed out before breakpoint installation could be confirmed"
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
9. 不把 lifecycle diagnostics 变成 material probe。
10. 不继续只输出 frida_attach_or_spawn_failed 而不写 lifecycle checkpoint。
11. 不把 subprocess timeout 当作 target launch 失败的充分证据；必须写出最后确认阶段。
12. 不建设通用 debugger backend / 通用多后端平台。
13. 不默认增加 timeout 来掩盖生命周期缺证。
14. 不把 stale/missing artifact 当 current evidence。
15. 不伪造 branch_eip / eflags / instruction / condition / next_eip。
16. 不读取完整 solve_reports/。
17. 不读取完整 PROJECT_PROGRESS_LOG.txt。
18. 不修改 .codex-skills/。
19. 不修改 sample_corpus/reverse/。
20. 不修改 reverse_agent/harness.py。
21. 不修改 reverse_agent/sample_solver.py。
22. 不提交完整 solve_reports/。
23. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 Frida breakpoint-only bounded control-flow surface。
3. 不要求也不默认实现 full single-step API。
4. 允许在 sidecar 内写 lifecycle checkpoint 与 flush-safe artifact。
5. 允许 wrapper 捕获 TimeoutExpired 并解析已有 per-candidate partial artifact/log。
6. 允许把同一个 subprocess timeout 细化为具体 lifecycle timeout。
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

必须读取或验证：

```text
.codex-skills/registry.json
project_state.artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
project_state.current_state.current_bottleneck
project_state/rounds/round_20260601_narrower_post_entry_breakpoint_audit/round_manifest.json
```

允许有界读取 current upstream artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_narrower_post_entry_breakpoint_audit/compare_handoff_narrower_post_entry_breakpoint_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json
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
13. 是否给每个候选写出 lifecycle checkpoint。
14. 是否能区分 subprocess timeout 发生的最后确认阶段。
15. 是否记录 candidate_invocation_health，包括 command、returncode、timed_out、stdout_tail、stderr_tail、partial_artifact_path、partial_artifact_exists、partial_artifact_size。
16. 是否记录 sidecar lifecycle，包括 dependency_import、target_exists、spawn_attempted/spawn_ok、attach_attempted/attach_ok、script_create/load、breakpoint_install、resume、ui_connect、ui_trigger、artifact_write。
17. 是否把 frida_attach_or_spawn_failed 细化为更具体 blocker；如果没有，是否明确 instrumentation gap。
18. 是否没有伪造 post_entry_events、branch_eip、EFLAGS、condition、next_eip。
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

### 6.1 Sidecar lifecycle checkpoints

增强：

```text
reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py
```

必须让 sidecar 在关键阶段写出 flush-safe partial artifact 或 log checkpoint：

```text
1. sidecar_started
2. arguments_parsed
3. target_checked
4. dependency_import_attempted
5. dependency_import_ok / dependency_import_failed
6. frida_spawn_attempted
7. frida_spawn_ok / frida_spawn_failed
8. frida_attach_attempted
9. frida_attach_ok / frida_attach_failed
10. script_create_attempted
11. script_create_ok / script_create_failed
12. script_load_attempted
13. script_load_ok / script_load_failed
14. breakpoint_install_attempted
15. breakpoint_install_ok / breakpoint_install_failed
16. frida_resume_attempted
17. frida_resume_ok / frida_resume_failed
18. ui_connect_attempted
19. ui_connect_ok / ui_connect_failed
20. ui_trigger_attempted
21. ui_trigger_ok / ui_trigger_failed
22. observation_wait_started
23. observation_wait_finished_or_timeout
24. final_artifact_write_attempted
25. final_artifact_write_ok / final_artifact_write_failed
```

如果 subprocess 被 wrapper timeout 杀死，已有 partial artifact 必须仍能说明最后确认阶段。

### 6.2 Wrapper timeout handling

增强 `CompareAwareSearchStrategy` 中当前 narrower audit runner 的 timeout fallback。

最小要求：

```text
1. 捕获 TimeoutExpired 后读取 candidate partial artifact 和 sidecar log。
2. 不直接把 timeout 全部归为 frida_attach_or_spawn_failed。
3. 根据 last_lifecycle_stage 细化 classification，例如 frida_spawn_timeout、frida_attach_timeout、script_load_timeout、breakpoint_install_timeout、ui_connect_timeout、ui_trigger_timeout。
4. 写入 candidate_invocation_health。
5. 如果 partial artifact 不存在，classification 才能是 subprocess_timeout_before_lifecycle_checkpoint，并标明 wrapper/sidecar gap。
6. 不提高默认 per_probe_timeout；如测试使用更小 timeout，只能用于 mock 或 bounded diagnostic。
```

### 6.3 Artifact schema additions

在现有 artifact 上 additive 增加字段，不删除旧字段：

```json
{
  "lifecycle_schema_version": 1,
  "lifecycle_diagnostics": {
    "classification": "...",
    "last_confirmed_stage": "...",
    "last_error_stage": "...",
    "timeout_stage": "...",
    "stage_counts": {},
    "candidate_invocation_health": {}
  },
  "candidates": [
    {
      "candidate_hex": "...",
      "lifecycle": {
        "last_confirmed_stage": "...",
        "last_error_stage": "...",
        "stages": []
      },
      "candidate_invocation_health": {
        "subprocess_returncode": 124,
        "subprocess_timed_out": true,
        "subprocess_stdout_tail": "...",
        "subprocess_stderr_tail": "...",
        "partial_artifact_path": "...",
        "partial_artifact_exists": true,
        "partial_artifact_size_bytes": 0
      },
      "classification": "..."
    }
  ]
}
```

仍必须保留：

```text
candidate_generation_changed=false
ranking_changed=false
search_budget_changed=false
beam_budget_topn_timeout_frontier_limit_expanded=false
breakpoint_probe_allowed=false
material_capture_allowed=false
crypto_hook_allowed=false
```

### 6.4 Project state projection

`project_state.py` 必须继续 additive 投影：

```text
artifact_index.latest_artifacts.compare_handoff_narrower_post_entry_breakpoint_audit
artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.stage=compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.reason=<specific lifecycle classification>
```

如果 classification 仍是 `frida_attach_or_spawn_failed`，必须附加：

```text
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.lifecycle_diagnostics.classification
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.lifecycle_diagnostics.last_confirmed_stage
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit.lifecycle_diagnostics.timeout_stage
```

不得删除旧 `compare_handoff_post_entry_step_runtime_audit`。不得把动态事实写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_narrower_post_entry_breakpoint_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "narrower_post_entry or spawn_attach or lifecycle"
python -m pytest -q tests\test_project_state.py -k "narrower_post_entry or spawn_attach or lifecycle or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果本地 runtime 可执行，必须额外运行一次 bounded artifact generation，但仍保持 3 个固定候选和现有 timeout，不做扩时实验：

```text
python -c "from pathlib import Path; from reverse_agent.strategies.compare_aware_search import run_compare_handoff_narrower_post_entry_breakpoint_audit; target=Path(r'F:\reverse-agent\solve_reports\samplereverse_patched.exe'); artifacts_dir=Path(r'solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_narrower_post_entry_breakpoint_audit'); result=run_compare_handoff_narrower_post_entry_breakpoint_audit(target=target, artifacts_dir=artifacts_dir, per_probe_timeout=2.2, source_payload={'source_run':'sr_arg0_hook_readiness_ordering_20260526_r1','classification':'frida_attach_or_spawn_failed'}, run_name='sr_arg0_hook_readiness_ordering_20260526_r1'); print(result['result_path']); print(result['payload'].get('classification')); print(result['payload'].get('lifecycle_diagnostics', {}))"
```

如果 runtime 环境仍不能执行，必须：

```text
1. 生成 blocked/partial artifact。
2. 写明更具体 blocker 或明确 wrapper/sidecar lifecycle gap。
3. 不伪造 breakpoint hits 或 post_entry_events。
4. 不把 runtime_sidecar_executed 写成 true，除非确实进入 sidecar lifecycle 并有 checkpoint 证据。
5. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_frida_spawn_attach_lifecycle_diagnostics
round_id=round_20260601_frida_spawn_attach_lifecycle_diagnostics
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
7. sidecar 无法写出任何 lifecycle checkpoint；输出 subprocess_timeout_before_lifecycle_checkpoint 或 candidate_artifact_write_failed 并停止。
8. Frida backend import 失败；输出 debugger_dependency_missing 并停止。
9. target 不存在或不可 launch；输出 target_missing_or_unlaunchable / frida_spawn_failed / frida_spawn_timeout 并停止。
10. attach 失败；输出 frida_attach_failed / frida_attach_timeout 并停止。
11. script load 失败；输出 script_create_or_load_failed / script_load_timeout 并停止。
12. 0x2338/0x1b50 breakpoint 无法安装；输出 breakpoint_install_failed / breakpoint_install_timeout 并停止。
13. 0x2338/0x1b50 breakpoint 安装成功但不命中；输出 entry_breakpoint_not_hit 并停止。
14. handoff_helper_entry 命中但 successor surface 不命中；输出 successor_breakpoint_not_hit 并停止。
15. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。

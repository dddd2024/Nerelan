```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260601_narrower_post_entry_breakpoint_audit",
  "round_id": "round_20260601_narrower_post_entry_breakpoint_audit",
  "based_on_state_build_id": "state_20260601_101227_0ec04ab18c9d",
  "based_on_state_digest": "0ec04ab18c9d7aeac6a1e284a67f7448e1b815ec86af1149c249ef5005651e8a",
  "status": "APPROVED",
  "mainline": "reverse_solving",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

本轮继续 **samplereverse 逆向解题主线**，但只做 `narrower_post_entry_breakpoint`。上一轮已经把笼统的 `runtime_unavailable` 精化为 `step_api_unavailable`：Frida import OK、target executable exists，但没有本地 Olly/Frida single-step implementation wired，breakpoint installation 也未实际尝试。

当前 Codex 实际执行权威是本文件 `project_state/decision_packet.md`。`project_state/task_packet.json` 中的 `task` / `derived_task` 只是状态派生建议，不能覆盖本 decision。

## 1. Goal

新增或增强一个有界 artifact：

```text
compare_handoff_narrower_post_entry_breakpoint_audit.json
```

核心目标：

```text
在 single-step API 不可用的前提下，不继续重复 step_api_unavailable 诊断；改用更窄的 Frida breakpoint-only 路线，验证 handoff_helper_entry 后是否能命中已知 bounded control-flow surfaces。
```

本轮必须回答：

```text
1. Frida backend 可导入且 target executable 存在时，是否能启动目标进程并安装 bounded breakpoint。
2. 0x2338 predecessor_handoff_call 与 0x1b50 handoff_helper_entry 是否能被安装并命中。
3. 在不使用 single-step 的情况下，是否能在 handoff_helper_entry 后命中至少一个 bounded successor surface。
4. 如果能命中 successor surface，记录每个固定候选的 event sequence、EIP/module_offset、hit order、exception/compare successor/actual compare 是否出现。
5. 如果不能命中，必须区分 target_launch_failed、breakpoint_install_failed、entry_breakpoint_not_hit、successor_breakpoint_not_hit、frida_attach_or_spawn_failed、instrumentation_gap_but_environment_verified。
6. 不得把本轮变成 Base64/RC4 probe、material capture、候选搜索或通用 debugger 平台建设。
```

本轮不是求最终 flag，不新增候选，不运行 Base64/RC4 breakpoint probe，不做 material capture，不做 crypto hook。

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
state_build_id=state_20260601_101227_0ec04ab18c9d
state_digest=0ec04ab18c9d7aeac6a1e284a67f7448e1b815ec86af1149c249ef5005651e8a
source_run=sr_arg0_hook_readiness_ordering_20260526_r1
```

当前 `task_packet.task` / `derived_task` 为状态派生建议：

```text
Repair bounded post-entry step instrumentation
```

它不是当前执行权威；本 decision 才是当前轮执行权威。

当前 bottleneck：

```text
stage=compare_handoff_post_entry_step_runtime_audit
blocker=step_api_unavailable
reason=step_api_unavailable
confidence=medium
```

current artifact：

```text
compare_handoff_post_entry_step_runtime_audit:
  freshness=current
  source_run=sr_arg0_hook_readiness_ordering_20260526_r1
  path=solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\reports\tool_artifacts\samplereverse_patched\compare_handoff_post_entry_step_runtime_audit\compare_handoff_post_entry_step_runtime_audit.json
  sha256=a7be53b5d1c855bcb4b2e9e7fa9c26bc700e5b6f0dc0ffc3ca10989f96bea849
```

上一轮 instrumentation rework 结论：

```text
classification=step_api_unavailable
overall_classification=step_api_unavailable
runtime_sidecar_executed=false
debugger_backend=frida
backend_import_ok=true
target_executable_exists=true
target_launch_attempted=false
breakpoint_install_attempted_count=0
breakpoint_install_ok_count=0
breakpoint_hit_count=0
step_api_available_count=0
next_bounded_action=narrower_post_entry_breakpoint
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

允许的 bounded breakpoint surface 只能来自 current project_state / current artifacts：

```text
1. predecessor_handoff_call: module+0x2338
2. handoff_helper_entry: module+0x1b50
3. process_exception: module+0x1913, only as exception/control-flow surface
4. compare successor / actual compare only if already encoded in current artifacts or existing strategy constants
```

不得从 stale artifact 中提取新的 current evidence；如必须提及旧 artifact，只能明确标记 stale/background，不得作为当前决策依据。

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
9. 不把 narrower post-entry breakpoint 变成 material probe。
10. 不继续只生成 step_api_unavailable 诊断而不尝试 bounded breakpoint install。
11. 不建设通用 debugger backend / 通用多后端平台。
12. 不把 stale/missing artifact 当 current evidence。
13. 不伪造 branch_eip / eflags / instruction / condition / next_eip。
14. 不读取完整 solve_reports/。
15. 不读取完整 PROJECT_PROGRESS_LOG.txt。
16. 不修改 .codex-skills/。
17. 不修改 sample_corpus/reverse/。
18. 不修改 reverse_agent/harness.py。
19. 不修改 reverse_agent/sample_solver.py。
20. 不提交完整 solve_reports/。
21. 不把 task_packet.task / derived_task 当成当前轮执行权威。
```

本轮允许 runtime 的边界：

```text
1. 必须使用同 3 个固定候选。
2. 只允许 Frida breakpoint-only bounded control-flow surface。
3. 不要求也不默认实现 full single-step API。
4. 如果能实现最小 single-step，也必须只用于 handoff_helper_entry 后 max_steps <= 32 的 control-flow surface。
5. 若无法启动 target 或安装 breakpoint，输出具体 blocker 并停止。
6. 不允许 dump 任意大内存，不允许保存 material bytes，不允许输出 candidate score/ranking。
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
project_state.artifact_index.latest_artifacts_v2.compare_handoff_post_entry_step_runtime_audit
project_state.current_state.latest_compare_handoff_post_entry_step_runtime_audit
project_state.current_state.current_bottleneck
project_state/rounds/round_20260601_post_entry_instrumentation_rework/round_manifest.json
```

允许有界读取 current upstream artifacts，但不得遍历完整 solve_reports：

```text
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_post_entry_step_runtime_audit/compare_handoff_post_entry_step_runtime_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_hook_surface_repair_audit/compare_handoff_hook_surface_repair_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_branch_operand_runtime_audit/compare_handoff_branch_operand_runtime_audit.json
solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/reports/tool_artifacts/samplereverse_patched/compare_handoff_path_divergence_audit/compare_handoff_path_divergence_audit.json
```

允许检查和修改：

```text
reverse_agent/olly_scripts/compare_handoff_post_entry_step_audit.py
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

不得修改：

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
6. compare_handoff_post_entry_step_runtime_audit freshness 是否为 current。
7. 是否保持同 3 个固定候选。
8. 是否没有新增候选、扩大 beam/topN/budget/timeout/frontier_limit。
9. 是否没有运行 Base64/RC4 breakpoint probe。
10. 是否没有运行 material capture / crypto hook。
11. 是否没有读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt。
12. 是否没有修改 .codex-skills/、sample_corpus/reverse/、harness.py、sample_solver.py。
13. 是否实际尝试 target launch 或明确说明无法 launch 的系统原因。
14. 是否实际尝试安装 bounded breakpoints，尤其 module+0x2338 与 module+0x1b50。
15. 是否记录 breakpoint_install_attempted / install_ok / hit / error。
16. 是否记录 per-candidate event_sequence。
17. 是否捕获到 handoff_helper_entry 后 successor surface；若没有，是否给出具体 blocker。
18. 是否没有伪造 post_entry_events、branch_eip、EFLAGS、next_eip。
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

### 6.1 Narrower breakpoint-only sidecar

优先新增：

```text
reverse_agent/olly_scripts/compare_handoff_narrower_post_entry_breakpoint_audit.py
```

也可以在现有 `compare_handoff_post_entry_step_audit.py` 中新增 `mode=narrower_post_entry_breakpoint`，但输出 artifact 名称必须可区分。

最小行为：

```text
1. 使用 Frida backend；不要求 single-step。
2. 验证 target executable path。
3. 尝试 spawn/attach target。
4. 对 3 个固定候选逐一运行。
5. 安装 bounded breakpoint：module+0x2338、module+0x1b50，以及 current artifacts 已确认的 successor/exception/control-flow surface。
6. 记录每个 breakpoint 的 install_attempted/install_ok/hit/error。
7. 记录 per-candidate event_sequence 和 first_divergence_after。
8. 如 handoff_helper_entry 命中但 successor surface 不命中，输出 successor_breakpoint_not_hit 或 instrumentation_gap_but_environment_verified。
```

### 6.2 Artifact schema

新增 artifact 最小 schema：

```json
{
  "schema_version": 1,
  "sample": "samplereverse",
  "source_run": "sr_arg0_hook_readiness_ordering_20260526_r1",
  "source_artifacts": [
    "compare_handoff_post_entry_step_runtime_audit",
    "compare_handoff_hook_surface_repair_audit",
    "compare_handoff_branch_operand_runtime_audit"
  ],
  "candidate_count": 3,
  "fixed_candidates": ["..."],
  "runtime_scope": {
    "mode": "narrower_post_entry_breakpoint",
    "debugger_backend": "frida",
    "single_step_required": false,
    "breakpoint_probe_allowed": false,
    "material_capture_allowed": false,
    "crypto_hook_allowed": false
  },
  "breakpoint_plan": [
    {"name": "predecessor_handoff_call", "module_offset": "0x2338"},
    {"name": "handoff_helper_entry", "module_offset": "0x1b50"}
  ],
  "candidates": [
    {
      "candidate_hex": "...",
      "target_launch": {
        "attempted": false,
        "ok": false,
        "error": ""
      },
      "breakpoints": [
        {
          "name": "handoff_helper_entry",
          "module_offset": "0x1b50",
          "install_attempted": false,
          "install_ok": false,
          "hit": false,
          "hit_order": null,
          "eip": "",
          "error": ""
        }
      ],
      "event_sequence": [],
      "handoff_helper_entry_observed": false,
      "successor_surface_observed": false,
      "process_exception_observed": false,
      "compare_successor_observed": false,
      "actual_compare_observed": false,
      "classification": "target_launch_failed | breakpoint_install_failed | entry_breakpoint_not_hit | successor_breakpoint_not_hit | post_entry_breakpoint_observed | instrumentation_gap_but_environment_verified"
    }
  ],
  "cross_candidate": {
    "classification": "...",
    "first_divergence_after": "",
    "breakpoint_hit_counts": {},
    "next_bounded_action": "..."
  },
  "candidate_generation_changed": false,
  "ranking_changed": false,
  "search_budget_changed": false,
  "beam_budget_topn_timeout_frontier_limit_expanded": false,
  "breakpoint_probe_allowed": false
}
```

### 6.3 Strategy integration

在 `CompareAwareSearchStrategy` 中新增有界入口，建议命名：

```text
compare_handoff_narrower_post_entry_breakpoint_audit
```

该入口只允许：

```text
1. 准备 3 个固定候选。
2. 调用 narrower breakpoint sidecar。
3. 写入 compare_handoff_narrower_post_entry_breakpoint_audit.json。
4. 更新 project_state artifact 索引。
```

不得触发：

```text
candidate generation
guided pool
SMT
frontier search
material probe
Base64/RC4 probe
old sample_solver
```

### 6.4 Project state 更新

若生成新 artifact，必须 additive 更新：

```text
artifact_index.latest_artifacts.compare_handoff_narrower_post_entry_breakpoint_audit
artifact_index.latest_artifacts_v2.compare_handoff_narrower_post_entry_breakpoint_audit
current_state.latest_compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.stage=compare_handoff_narrower_post_entry_breakpoint_audit
current_state.current_bottleneck.reason=<specific classification>
```

不得删除旧 `compare_handoff_post_entry_step_runtime_audit`。不得把动态事实写入 `.codex-skills/`。

## 7. Tests

必须运行并记录到 `project_state/pytest_result.txt`：

```text
python -m py_compile reverse_agent\strategies\compare_aware_search.py reverse_agent\project_state.py reverse_agent\olly_scripts\compare_handoff_post_entry_step_audit.py reverse_agent\olly_scripts\compare_handoff_narrower_post_entry_breakpoint_audit.py
python -m pytest -q tests\test_compare_aware_search_strategy.py -k "narrower_post_entry or post_entry_step or instrumentation"
python -m pytest -q tests\test_project_state.py -k "narrower_post_entry or post_entry_step or artifact_index"
python -m reverse_agent.project_state build --reports-dir solve_reports --sample samplereverse --run-name sr_arg0_hook_readiness_ordering_20260526_r1
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
git diff --check
```

如果 runtime 环境仍不能执行，必须：

```text
1. 生成 blocked artifact。
2. 写明具体 blocker：target_launch_failed / frida_attach_or_spawn_failed / breakpoint_install_failed / entry_breakpoint_not_hit。
3. 不伪造 breakpoint hits 或 post_entry_events。
4. 不把 runtime_sidecar_executed 写成 true。
5. report status 使用 BLOCKED 或 PARTIAL，不得使用 SUCCESS / ACCEPTED。
```

Codex report 顶部必须包含 `codex_report_summary`，且：

```text
based_on_decision_id=decision_20260601_narrower_post_entry_breakpoint_audit
round_id=round_20260601_narrower_post_entry_breakpoint_audit
```

`pytest_result.txt` 顶部必须包含 `pytest_result_summary`，且 decision_id/report_id/round_id 与 report 匹配。

## 8. Stop Conditions

遇到以下情况必须停止并报告，不得继续扩大范围：

```text
1. artifact_index.latest_artifacts_v2 中 compare_handoff_post_entry_step_runtime_audit 不是 current。
2. 3 个固定候选无法全部保留。
3. 需要新增候选、扩大 beam/topN/budget/timeout/frontier_limit 才能继续。
4. 需要运行 Base64/RC4 breakpoint probe 或 material capture 才能继续。
5. 需要读取完整 solve_reports/ 或 PROJECT_PROGRESS_LOG.txt 才能继续。
6. 发现必须修改 .codex-skills/、sample_corpus/reverse/、harness.py 或 sample_solver.py 才能继续。
7. Frida backend import 失败；输出 debugger_backend_missing 并停止。
8. target 无法 launch/attach；输出 target_launch_failed 或 frida_attach_or_spawn_failed 并停止。
9. 0x2338/0x1b50 breakpoint 无法安装；输出 breakpoint_install_failed 并停止。
10. 0x2338/0x1b50 breakpoint 安装成功但不命中；输出 entry_breakpoint_not_hit 并停止。
11. handoff_helper_entry 命中但 successor surface 不命中；输出 successor_breakpoint_not_hit 或 instrumentation_gap_but_environment_verified 并停止。
12. lint-decision / lint-report / pytest_result 无法与当前 decision_id 对齐。
```

如果 stop condition 触发，Codex 必须在 `codex_execution_report.md` 中给出 `status=BLOCKED` 或 `PARTIAL`，并说明缺失的最小证据；不得声称 ACCEPTED。
